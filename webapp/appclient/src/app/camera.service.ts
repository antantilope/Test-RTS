
import { Injectable } from '@angular/core';
import { loggers } from 'winston';

import { ApiService } from './api.service';
import { BoxCoords } from './models/box-coords.model';
import { DrawableCanvasItems, DrawableShip, ScannerDataElement } from './models/drawable-objects.model';
import { PointCoord } from './models/point-coord.model';



/* CAMERA_MODE_SHIP Camera Position automatically follows the ships coords. */
export const CAMERA_MODE_SHIP = 'ship'

/* CAMERA_MODE_SCANNER Camera Position AND zoom automatically adjusts to show ship and scanner data. */
export const CAMERA_MODE_SCANNER = 'scanner'

/* CAMERA_MODE_FREE Camera Position AND zoom are manually adjusted by the user. */
export const CAMERA_MODE_FREE = 'free'



const MAX_ZOOM_MANUAL = 10000


@Injectable({
  providedIn: 'root'
})
export class CameraService {

  public canvasWidth: number = 0
  public canvasHeight: number = 0
  public canvasHalfWidth: number = 0
  public canvasHalfHeight: number = 0

  /*
    Zoom is an integer.
    1 is the most zoomed in.
    "Zooming out" increases this value
  */
  private zoom: number = 10;
  private zoomLevels = [1, 5, 10, 17, 25, 50, 100, 250, 500, 1000, 2000, 5000, 10000, 25000, 50000, 100000]
  private zoomIndex = this.zoomLevels.indexOf(this.zoom)
  private finalZoomIndex = this.zoomLevels.length - 1

  private xPosition: number = null;
  private yPosition: number = null;
  private mode = CAMERA_MODE_FREE;

  constructor(
    private _api: ApiService,
  ) {
  }

  public setCanvasWidthHeight(width: number, height: number) {
    this.canvasWidth = width
    this.canvasHeight = height
    this.canvasHalfWidth = Number((width / 2).toFixed())
    this.canvasHalfHeight = Number((height / 2).toFixed())
  }

  public getZoom(): number {
    return this.zoom
  }

  public canManualZoom(): boolean {
    return this.mode !== CAMERA_MODE_SCANNER
  }

  public canManualPan(): boolean {
    return this.mode === CAMERA_MODE_FREE
  }



  public adjustZoom(zoomIn: boolean): void {
    if(zoomIn) {
      if (this.zoomIndex > 1) {
        this.zoomIndex--
        this.zoom = this.zoomLevels[this.zoomIndex]
      }
    } else if (!zoomIn) {
      if(this.zoomIndex < this.finalZoomIndex) {
        this.zoomIndex++
        this.zoom = this.zoomLevels[this.zoomIndex]
      }
    }
  }

  public xPan(delta: number): void {
    this.xPosition += delta
  }

  public yPan(delta: number): void {
    this.yPosition += delta
  }

  public setPosition(x: number, y: number) : void {
    this.xPosition = x
    this.yPosition = y
  }

  public getPosition(): PointCoord {
    return {x: this.xPosition, y: this.yPosition}
  }

  public getMode(): string {
    return this.mode
  }
  public setModeShip(): void {
    this.mode = CAMERA_MODE_SHIP
    this.setZoomToNearestLevel()
  }
  public setModeScanner(): void {
    this.mode = CAMERA_MODE_SCANNER
  }
  public setModeFree(): void {
    this.mode = CAMERA_MODE_FREE
    this.setZoomToNearestLevel()
  }
  public setZoomToNearestLevel(): void {
    for(let i in this.zoomLevels) {
      if(this.zoom <= this.zoomLevels[i]) {
        this.zoom = this.zoomLevels[i]
        this.zoomIndex = parseInt(i)
        return
      }
    }
    this.zoom = this.zoomLevels[this.finalZoomIndex]
    this.zoomIndex = this.finalZoomIndex
  }

  private getCameraMapBoxCoords(): BoxCoords {
    /* Return coords that describe which part of the game map are visible on the canvas.
    */
    const x1 = this.xPosition - (this.canvasHalfWidth * this.zoom)
    const y1 = this.yPosition - (this.canvasHalfHeight * this.zoom)
    const x2 = this.xPosition + (this.canvasHalfWidth * this.zoom)
    const y2 = this.yPosition + (this.canvasHalfHeight * this.zoom)
    return {x1, y1, x2, y2}
  }

  private rectCoordsToBoxCoords(
    p0: PointCoord,
    p1: PointCoord,
    p2: PointCoord,
    p3: PointCoord,
    buffer: number = 0,
  ): BoxCoords {
    return {
      x1: Math.min(p0.x, p1.x, p2.x, p3.x) - buffer,
      y1: Math.min(p0.y, p1.y, p2.y, p3.y) - buffer,
      x2: Math.max(p0.x, p1.x, p2.x, p3.x) + buffer,
      y2: Math.max(p0.y, p1.y, p2.y, p3.y) + buffer,
    }
  }

  private coordToBoxCoord(point: PointCoord, buffer: number = 0): BoxCoords {
    return {
      x1: point.x - buffer,
      y1: point.y - buffer,
      x2: point.x + buffer,
      y2: point.y + buffer,
    }
  }

  private relativeCoordToAbsoluteCoord(relative: PointCoord, origin: PointCoord): PointCoord {
    return {
      x: origin.x + relative.x,
      y: origin.y + relative.y,
    }
  }

  private arrayToCoords(coords: number[]): PointCoord {
    return {x: coords[0], y: coords[1]}
  }

  private boxesOverlap(box1: BoxCoords, box2: BoxCoords): boolean {
    const completeXOverlap = (box1.x1 <= box2.x1) && (box1.x2 >= box2.x2)
    const completeYOverlap = (box1.y1 <= box2.y1) && (box1.y2 >= box2.y2)
    if(completeXOverlap && completeYOverlap) {
      return true
    }
    const box1X1InBox2 = box1.x1 >= box2.x1 && box1.x1 <= box2.x2
    const box1Y1InBox2 = box1.y1 >= box2.y1 && box1.y1 <= box2.y2
    const box1X2InBox2 = box1.x2 >= box2.x1 && box1.x2 <= box2.x2
    const box1Y2InBox2 = box1.y2 >= box2.y1 && box1.y2 <= box2.y2
    if((box1X1InBox2 || box1X2InBox2) && (box1Y1InBox2 || box1Y2InBox2)) {
      return true
    }
    if(completeXOverlap && (box1Y1InBox2 || box1Y2InBox2)) {
      return true
    }
    if(completeYOverlap && (box1X1InBox2 || box1Y2InBox2)) {
      return true
    }
    return false
  }

  public mapCoordToCanvasCoord(mapCoord: PointCoord, origin: PointCoord): PointCoord {
    const mapDx = mapCoord.x - origin.x
    const mapDy = mapCoord.y - origin.y
    const camDx = Math.round(mapDx / this.zoom)
    const camDy = Math.round(mapDy / this.zoom)
    return {
      x: camDx + this.canvasHalfWidth,
      /* Must reorient Y coord
         because canvas origin is top left, where as map origin is bottom left.
      */
      y: this.canvasHeight - (camDy + this.canvasHalfHeight),
    }
  }

  public setCameraPositionAndZoomForScannerMode() {

  }

  public getDrawableCanvasObjects(): DrawableCanvasItems {
    /* Get objects to draw on the canvas.
        All coordinate points returned by the function are CANVAS coordinates.
    */

    const cameraMapBoxCoords: BoxCoords = this.getCameraMapBoxCoords()

    // Ship
    const ship: any = this._api.frameData.ship
    const shipCoord: PointCoord = {x: ship.coord_x, y: ship.coord_y}
    const shipMapCoordP0: PointCoord = this.relativeCoordToAbsoluteCoord(
      this.arrayToCoords(ship.rel_rot_coord_0),
      shipCoord,
    )
    const shipMapCoordP1: PointCoord = this.relativeCoordToAbsoluteCoord(
      this.arrayToCoords(ship.rel_rot_coord_1),
      shipCoord,
    )
    const shipMapCoordP2: PointCoord = this.relativeCoordToAbsoluteCoord(
      this.arrayToCoords(ship.rel_rot_coord_2),
      shipCoord,
    )
    const shipMapCoordP3: PointCoord = this.relativeCoordToAbsoluteCoord(
      this.arrayToCoords(ship.rel_rot_coord_3),
      shipCoord,
    )
    const shipMapBoxCoords: BoxCoords = this.rectCoordsToBoxCoords(
      shipMapCoordP0,
      shipMapCoordP1,
      shipMapCoordP2,
      shipMapCoordP3
    )

    const drawableItems: DrawableCanvasItems = {
      ships: [],
      ebeamRays: [],
    }
    const cameraPosition: PointCoord = this.getPosition()

    // Add own ship to drawable ships array
    if (this.boxesOverlap(shipMapBoxCoords, cameraMapBoxCoords)) {


      const overlayCenter = this.mapCoordToCanvasCoord({x: ship.coord_x, y:ship.coord_y}, cameraPosition)
      drawableItems.ships.push({
        isSelf: true,
        designator: "you",
        canvasCoordP0: this.mapCoordToCanvasCoord(shipMapCoordP0, cameraPosition),
        canvasCoordP1: this.mapCoordToCanvasCoord(shipMapCoordP1, cameraPosition),
        canvasCoordP2: this.mapCoordToCanvasCoord(shipMapCoordP2, cameraPosition),
        canvasCoordP3: this.mapCoordToCanvasCoord(shipMapCoordP3, cameraPosition),
        canvasCoordFin0P0: this.mapCoordToCanvasCoord(this.relativeCoordToAbsoluteCoord(this.arrayToCoords(ship.fin_0_rel_rot_coord_0), shipCoord), cameraPosition),
        canvasCoordFin0P1: this.mapCoordToCanvasCoord(this.relativeCoordToAbsoluteCoord(this.arrayToCoords(ship.fin_0_rel_rot_coord_1), shipCoord), cameraPosition),
        canvasCoordFin1P0: this.mapCoordToCanvasCoord(this.relativeCoordToAbsoluteCoord(this.arrayToCoords(ship.fin_1_rel_rot_coord_0), shipCoord), cameraPosition),
        canvasCoordFin1P1: this.mapCoordToCanvasCoord(this.relativeCoordToAbsoluteCoord(this.arrayToCoords(ship.fin_1_rel_rot_coord_1), shipCoord), cameraPosition),
        canvasCoordCenter: this.mapCoordToCanvasCoord(shipCoord, cameraPosition),
        engineLit: ship.engine_lit,
        fillColor: "#919191",
        shipId: ship.id,
      })

      if(ship.reaction_wheel_online) {
        const headingRads = ship.heading * (Math.PI / 180)
        drawableItems.reactionWheelOverlay = {
          centerCanvasCoord: overlayCenter,
          radiusPx: Math.round(this.canvasHeight / 6),
          compassPoint0: overlayCenter,
          compassPoint1: {
            x: overlayCenter.x + Math.round((this.canvasHeight / 5) * Math.sin(headingRads)),
            y: overlayCenter.y - Math.round((this.canvasHeight / 5) * Math.cos(headingRads)),
          }
        }
      }

      const velocityRadians = this.getCanvasAngleBetween(
        {x:0, y:0},
        {
          x: Math.round(ship.velocity_x_meters_per_second * 1000),
          y: Math.round(ship.velocity_y_meters_per_second * 1000),
        }
      )  * (Math.PI / 180)

      if(ship.engine_online && (ship.velocity_x_meters_per_second || ship.velocity_y_meters_per_second)) {

        drawableItems.engineOverlay = {
          vectorPoint0: overlayCenter,
          vectorPoint1: {
            x: overlayCenter.x + Math.round((this.canvasHeight / 4) * Math.sin(velocityRadians)),
            y: overlayCenter.y + Math.round((this.canvasHeight / 4) * Math.cos(velocityRadians)), // TODO: Why is this + and not -
          },
          metersPerSecond: Math.sqrt(
            Math.pow(ship.velocity_x_meters_per_second, 2)
            + Math.pow(ship.velocity_y_meters_per_second, 2)
          ).toFixed(2),
        }
      }

    }

    // Draw other scanner elements
    const boundingBoxBuffer = 10
    for(let i in ship.scanner_data) {
      const scannerData: ScannerDataElement = ship.scanner_data[i]
      if (scannerData.element_type === 'ship') {
        let drawableShip: DrawableShip = {
          isSelf: false,
          shipId: scannerData.id,
          canvasCoordCenter: this.mapCoordToCanvasCoord({
            x: scannerData.coord_x,
            y: scannerData.coord_y,
          }, cameraPosition),
          designator: scannerData.designator,
        }
        if(scannerData.visual_shape) {
          // Ship is within visual range

          const canvasCoordP0 = this.mapCoordToCanvasCoord({
            x: scannerData.visual_p0[0],
            y: scannerData.visual_p0[1],
          }, cameraPosition)
          const canvasCoordP1 = this.mapCoordToCanvasCoord({
            x: scannerData.visual_p1[0],
            y: scannerData.visual_p1[1],
          }, cameraPosition)
          const canvasCoordP2 = this.mapCoordToCanvasCoord({
            x: scannerData.visual_p2[0],
            y: scannerData.visual_p2[1],
          }, cameraPosition)
          const canvasCoordP3 = this.mapCoordToCanvasCoord({
            x: scannerData.visual_p3[0],
            y: scannerData.visual_p3[1],
          }, cameraPosition)

          const canvasCoordFin0P0 = this.mapCoordToCanvasCoord({
            x: scannerData.visual_fin_0_rel_rot_coord_0[0],
            y: scannerData.visual_fin_0_rel_rot_coord_0[1],
          }, cameraPosition)
          const canvasCoordFin0P1 = this.mapCoordToCanvasCoord({
            x: scannerData.visual_fin_0_rel_rot_coord_1[0],
            y: scannerData.visual_fin_0_rel_rot_coord_1[1],
          }, cameraPosition)
          const canvasCoordFin1P0 = this.mapCoordToCanvasCoord({
            x: scannerData.visual_fin_1_rel_rot_coord_0[0],
            y: scannerData.visual_fin_1_rel_rot_coord_0[1],
          }, cameraPosition)
          const canvasCoordFin1P1 = this.mapCoordToCanvasCoord({
            x: scannerData.visual_fin_1_rel_rot_coord_1[0],
            y: scannerData.visual_fin_1_rel_rot_coord_1[1],
          }, cameraPosition)

          drawableShip = {
            canvasCoordP0,
            canvasCoordP1,
            canvasCoordP2,
            canvasCoordP3,
            canvasCoordFin0P0,
            canvasCoordFin0P1,
            canvasCoordFin1P0,
            canvasCoordFin1P1,
            canvasBoundingBox: this.rectCoordsToBoxCoords(canvasCoordP0, canvasCoordP1, canvasCoordP2, canvasCoordP3, boundingBoxBuffer),
            engineLit: scannerData.visual_engine_lit,
            fillColor: scannerData.visual_fill_color,
            ...drawableShip
          }
        }
        else {
          // Ship is not within visual range
          drawableShip.canvasBoundingBox = this.coordToBoxCoord(drawableShip.canvasCoordCenter, 25)
        }

        if(scannerData.distance) {
          drawableShip.distance = scannerData.distance
          drawableShip.relativeHeading = scannerData.relative_heading
        }
        if(scannerData.thermal_signature) {
          drawableShip.thermalSignature = scannerData.thermal_signature
        }
        drawableItems.ships.push(drawableShip)

      }
    }

    // Add Energy Beam Rays
    for (let i in this._api.frameData.ebeam_rays) {
      let ray = this._api.frameData.ebeam_rays[i]
      drawableItems.ebeamRays.push({
        startPoint: this.mapCoordToCanvasCoord({x:ray.start_point[0], y:ray.start_point[1]}, cameraPosition),
        endPoint: this.mapCoordToCanvasCoord({x:ray.end_point[0], y:ray.end_point[1]}, cameraPosition),
        color: ray.color
      })
    }

    return drawableItems
  }

  public getEBeamLineThickness(): number {
    return 4
  }


  // GEOMETRY HELPERS // // // //

  private invertAngle(angle: number): number {
    return angle >= 180 ? angle - 180 : angle + 180
  }

  private signedAngleToUnsignedAngle(angle: number): number {
    if (angle >= 0) {
      return angle % 360
    }
    const posAngle = Math.abs(angle)
    if (posAngle <= 360) {
      return 360 - posAngle
    } else {
      return 360 - (posAngle % 360)
    }
  }

  public getCanvasAngleBetween(canvasPointA: PointCoord, canvasPointB: PointCoord): number {
    const dx = canvasPointB.x - canvasPointA.x
    const dy = (this.canvasHeight - canvasPointB.y) - (this.canvasHeight - canvasPointA.y)
    if(dx === 0 && dy === 0) {
      return 0
    }
    let angle;
    if (dy !== 0) {
      angle = Math.atan(dx / dy) * (180 / Math.PI)
    }
    else if (dy === 0 && dx > 0) {
      angle = 90
    }
    else if (dy === 0 && dx < 0) {
      angle = 270
    }
    else {
      throw new Error("not implemented")
    }

    const xNegative = dx < 0
    const yNegative = dy < 0
    const bothPositive = Boolean((!xNegative) && (!yNegative))
    const bothNegative = Boolean(xNegative && yNegative)
    if(bothPositive) {
      return Math.round(angle)
    }
    else if(bothNegative) {
      return Math.round(this.invertAngle(angle))
    }
    else if (yNegative) {
      return this.signedAngleToUnsignedAngle(this.invertAngle(Math.round(angle)))
    }
    else if (xNegative) {
      return this.signedAngleToUnsignedAngle(Math.round(angle))
    }
    else {
      throw new Error("Not Implemented")
    }

  }

}
