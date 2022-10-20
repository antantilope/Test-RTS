
import { Injectable } from '@angular/core';

import { ApiService } from './api.service';
import { BoxCoords } from './models/box-coords.model';
import {
  DrawableCanvasItems,
  DrawableShip,
  DrawableMagnetMineTargetingLine
} from './models/drawable-objects.model';
import { PointCoord } from './models/point-coord.model';
import { ScannerDataShipElement, Ship } from './models/apidata.model';
import { MAGNET_MINE_SIDE_LENGTH_METERS } from "./constants"

function getRandomFloat(min: number, max: number): number {
  return Math.random() * (max - min) + min;
}

/* Camera used  */
export const CAMERA_NAME_GAME_DISPLAY = 'GAMEDISPLAY'
export const CAMERA_NAME_SCANNER_DISPLAY = 'SCANNERDISPLAY'

export class Camera {
  // A camera points at a position on the map (absolute coordinate)
  // and provides methods to orient pixels on a canvas.


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
  private zoomLevels = [5, 7, 10, 15, 17, 20, 25, 27, 30, 35, 37, 40]
  private zoomIndex = this.zoomLevels.indexOf(this.zoom)
  private finalZoomIndex = this.zoomLevels.length - 1

  private xPosition: number = null;
  private yPosition: number = null;

  // If in element width/height is smaller than this size,
  // represent it with a dot to ensure it is clearly visible.
  public minSizeForDotPx = 6;

  private framesToShowBoostedEngine = 5


  constructor(
    public name: string,
    private _api: ApiService,
  ) {}


  public setCanvasWidthHeight(width: number, height: number) {
    this.canvasWidth = width
    this.canvasHeight = height
    this.canvasHalfWidth = Number((width / 2).toFixed())
    this.canvasHalfHeight = Number((height / 2).toFixed())
  }

  public getZoom(): number {
    return this.zoom
  }

  public getMaxZoom(): number {
    return Math.max(...this.zoomLevels)
  }
  public getMinZoom(): number {
    return Math.min(...this.zoomLevels)
  }


  public setZoom(zoom: number) {
    this.zoom = zoom
  }

  public setMiddleZoom() {
    this.setZoom(this.zoomLevels[Math.floor(
      this.zoomLevels.length / 2
    )])
  }

  public adjustZoom(zoomIn: boolean): void {
    if(zoomIn) {
      if (this.zoomIndex > 0) {
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

  public setZoomIndex(ix: number) {
    if(ix >= this.zoomLevels.length) {
      return console.warn("invalid zoom index " + ix)
    }
    this.zoom = this.zoomLevels[ix]
    this.zoomIndex = ix
  }

  public getZoomIndex(): number | null {
    return this.zoomIndex
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

  private pointCoordToBoxCoord(point: PointCoord, buffer: number): BoxCoords {
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

  public setCameraPositionAndZoomForScannerMode(scannerTargetIDCursor: string | null) {
    const ship = this._api.frameData.ship
    if(!scannerTargetIDCursor && ship.scanner_locked && ship.scanner_lock_target) {
      // No scanner cursor and scanner is locked on a target
      this.setCameraPositionAndZoomShowShipAndTarget(ship.scanner_lock_target)
    }
    else if (scannerTargetIDCursor) {
      // Scanner cursor is pointed at locked on target
      this.setCameraPositionAndZoomShowShipAndTarget(scannerTargetIDCursor)
    }
    else {
      // Scanner may be locked but the cursor is set on another ship.
      this.setCameraPositionAndZoomShowShipVision()
    }
  }

  private setCameraPositionAndZoomShowShipVision() {
    const ship = this._api.frameData.ship
    this.setPosition(
      ship.coord_x,
      ship.coord_y,
    )
    // Map units.
    const maxVisionRadius = Math.max(
      ship.visual_range,
      ship.scanner_online && ship.scanner_mode == 'ir' ? ship.scanner_ir_range : 0,
      ship.scanner_online && ship.scanner_mode == 'radar' ? ship.scanner_radar_range : 0,
    )
    // Canvas pixels.
    const canvasRadius = Math.min(
      this.canvasHalfHeight,
      this.canvasHalfWidth,
    )
    this.zoom = Math.ceil(maxVisionRadius / canvasRadius * this._api.frameData.map_config.units_per_meter)

  }
  private setCameraPositionAndZoomShowShipAndTarget(scannerTargetIDCursor: string){
    const ship = this._api.frameData.ship
    // Point camera between ship and target
    const scannerData = ship.scanner_ship_data.find(sd => sd.id == scannerTargetIDCursor)
    if(!scannerData) {
      return this.setCameraPositionAndZoomShowShipVision()
    }
    const tx = scannerData.coord_x
    const ty = scannerData.coord_y
    const sx = ship.coord_x
    const sy = ship.coord_y
    const cx = Math.floor((tx + sx) / 2)
    const cy = Math.floor((ty + sy) / 2)
    this.setPosition(cx, cy)

    // Set zoom level to show both ship and target
    // Canvas pixels.
    const canvasRadius = Math.floor(Math.min(
      this.canvasHalfHeight,
      this.canvasHalfWidth,
    ) * 0.85)
    // Map units.
    let halfDistance = Math.sqrt(Math.pow(sx - tx, 2) + Math.pow(sy - ty, 2)) / 2
    halfDistance = halfDistance - this._api.frameData.map_config.units_per_meter
    this.zoom = halfDistance / canvasRadius
  }


  public getDrawableCanvasObjects(): DrawableCanvasItems {
    /* Get objects to draw on the canvas.
        All coordinate points returned by the function are CANVAS coordinates.
    */

    const cameraMapBoxCoords: BoxCoords = this.getCameraMapBoxCoords()

    // Ship
    const ship: Ship = this._api.frameData.ship
    const mapConfig = this._api.frameData.map_config
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
      magnetMines: [],
      magnetMineTargetingLines: [],
      ebeamRays: [],
      visionCircles:[],
    }
    const cameraPosition: PointCoord = this.getPosition()


    // Add vision circles in largest to smallest order
    const shipCanvasCoord = this.mapCoordToCanvasCoord(shipCoord, cameraPosition)
    const basicVisualRangeCanvasPxRadius = Math.round(
      (this._api.frameData.map_config.units_per_meter
      * this._api.frameData.ship.visual_range) / this.getZoom()
    )
    drawableItems.visionCircles.push({
      canvasCoord: shipCanvasCoord,
      radius: basicVisualRangeCanvasPxRadius,
      color: "#121212", // Dark gray
      name: 'eyes',
    })

    // Add map wall\
    const corner2 = this.mapCoordToCanvasCoord({x:mapConfig.x_unit_length, y:mapConfig.y_unit_length}, cameraPosition)
    const corner1 = this.mapCoordToCanvasCoord({x:0, y:0}, cameraPosition)
    drawableItems.mapWall = {
      x1: corner1.x,
      x2: corner2.x,
      y1: corner1.y,
      y2: corner2.y,
    }

    let canvasCoordP0 = this.mapCoordToCanvasCoord(shipMapCoordP0, cameraPosition)
    let canvasCoordP1 = this.mapCoordToCanvasCoord(shipMapCoordP1, cameraPosition)
    let canvasCoordP2 = this.mapCoordToCanvasCoord(shipMapCoordP2, cameraPosition)
    let canvasCoordP3 = this.mapCoordToCanvasCoord(shipMapCoordP3, cameraPosition)

    // Add own ship to drawable ships array
    drawableItems.ships.push({
      isSelf: true,
      alive: ship.alive,
      designator: "you",
      canvasCoordP0: canvasCoordP0,
      canvasCoordP1: canvasCoordP1,
      canvasCoordP2: canvasCoordP2,
      canvasCoordP3: canvasCoordP3,
      canvasCoordFin0P0: this.mapCoordToCanvasCoord(this.relativeCoordToAbsoluteCoord(this.arrayToCoords(ship.fin_0_rel_rot_coord_0), shipCoord), cameraPosition),
      canvasCoordFin0P1: this.mapCoordToCanvasCoord(this.relativeCoordToAbsoluteCoord(this.arrayToCoords(ship.fin_0_rel_rot_coord_1), shipCoord), cameraPosition),
      canvasCoordFin1P0: this.mapCoordToCanvasCoord(this.relativeCoordToAbsoluteCoord(this.arrayToCoords(ship.fin_1_rel_rot_coord_0), shipCoord), cameraPosition),
      canvasCoordFin1P1: this.mapCoordToCanvasCoord(this.relativeCoordToAbsoluteCoord(this.arrayToCoords(ship.fin_1_rel_rot_coord_1), shipCoord), cameraPosition),
      canvasCoordCenter: this.mapCoordToCanvasCoord(shipCoord, cameraPosition),
      engineLit: ship.engine_lit,
      engineBoosted: (this._api.frameData.game_frame - ship.engine_boosted_last_frame) <= this.framesToShowBoostedEngine,
      fillColor: "#919191",
      shipId: ship.id,
      aflame: ship.aflame,
      exploded: ship.exploded,
      gravityBrakePosition: ship.gravity_brake_position,
      gravityBrakeDeployedPosition: ship.gravity_brake_deployed_position,
      gravityBrakeActive: ship.gravity_brake_active,
      miningOreLocation: ship.mining_ore ? ship.parked_at_ore_mine : null,
      fuelingAtStation: ship.fueling_at_station,
      visualEbeamCharging: ship.ebeam_charging,
      lastTubeFireFrame: ship.last_tube_fire_frame,
      inVisualRange: true,
      canvasBoundingBox: this.rectCoordsToBoxCoords(
        canvasCoordP0,
        canvasCoordP1,
        canvasCoordP2,
        canvasCoordP3,
        15,
      )
    })
    if (
      Math.abs(
        drawableItems.ships[0].canvasCoordP1.x
        - drawableItems.ships[0].canvasCoordP2.x
      ) <= this.minSizeForDotPx
      && ship.alive
    ) {
      drawableItems.ships[0].isDot = true
    }

    // Draw other scanner elements
    // Other Ships
    const boundingBoxBuffer = 10
    for(let i in ship.scanner_ship_data) {
      const scannerData: ScannerDataShipElement = ship.scanner_ship_data[i]
      let canvasCoordP0 = this.mapCoordToCanvasCoord({
        x: scannerData.visual_p0[0],
        y: scannerData.visual_p0[1],
      }, cameraPosition)
      let canvasCoordP1 = this.mapCoordToCanvasCoord({
        x: scannerData.visual_p1[0],
        y: scannerData.visual_p1[1],
      }, cameraPosition)
      let canvasCoordP2 = this.mapCoordToCanvasCoord({
        x: scannerData.visual_p2[0],
        y: scannerData.visual_p2[1],
      }, cameraPosition)
      let canvasCoordP3 = this.mapCoordToCanvasCoord({
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

      let drawableShip: DrawableShip = {
        isSelf: false,
        isDot: scannerData.alive && Math.abs(canvasCoordP1.x - canvasCoordP2.x) <= this.minSizeForDotPx,
        alive: scannerData.alive,
        aflame: scannerData.aflame,
        exploded: scannerData.exploded,
        shipId: scannerData.id,
        canvasCoordCenter: this.mapCoordToCanvasCoord({
          x: scannerData.coord_x,
          y: scannerData.coord_y,
        }, cameraPosition),
        designator: scannerData.designator,
        inVisualRange: scannerData.in_visual_range,
        canvasCoordP0: canvasCoordP0,
        canvasCoordP1: canvasCoordP1,
        canvasCoordP2: canvasCoordP2,
        canvasCoordP3: canvasCoordP3,
        visualEbeamCharging: scannerData.visual_ebeam_charging,
        canvasCoordFin0P0,
        canvasCoordFin0P1,
        canvasCoordFin1P0,
        canvasCoordFin1P1,
        canvasBoundingBox: this.rectCoordsToBoxCoords(canvasCoordP0, canvasCoordP1, canvasCoordP2, canvasCoordP3, boundingBoxBuffer),
        engineLit: scannerData.visual_engine_lit,
        engineBoosted: (this._api.frameData.game_frame - scannerData.visual_engine_boosted_last_frame) <= this.framesToShowBoostedEngine,
        fillColor: scannerData.visual_fill_color,
        gravityBrakePosition: scannerData.visual_gravity_brake_position,
        gravityBrakeDeployedPosition: scannerData.visual_gravity_brake_deployed_position,
        gravityBrakeActive: scannerData.visual_gravity_brake_active,
        miningOreLocation: scannerData.visual_mining_ore_location,
        fuelingAtStation: scannerData.visual_fueling_at_station,
        lastTubeFireFrame: scannerData.visual_last_tube_fire_frame,
      }
      drawableItems.ships.push(drawableShip)
    }

    // Magnet mines
    const mineSideLenPx = MAGNET_MINE_SIDE_LENGTH_METERS * mapConfig.units_per_meter / this.getZoom()
    const mineHalfSideLenPx = mineSideLenPx / 2
    for(let i in ship.scanner_magnet_mine_data) {
      let mm = ship.scanner_magnet_mine_data[i]
      if(mm.exploded) {
        continue
      }
      let canvasCoordCenter = this.mapCoordToCanvasCoord(
        {x: mm.coord_x, y: mm.coord_y},
        cameraPosition,
      )
      let canvasX1 = canvasCoordCenter.x - mineHalfSideLenPx
      let canvasY1 = canvasCoordCenter.y - mineHalfSideLenPx
      drawableItems.magnetMines.push({
        mineId: mm.id,
        percentArmed: mm.percent_armed,
        isDot: mineSideLenPx <= this.minSizeForDotPx,
        canvasCoordCenter,
        canvasX1,
        canvasY1,
        canvasW: mineSideLenPx,
        canvasH: mineSideLenPx,
        canvasBoundingBox: this.pointCoordToBoxCoord(
          canvasCoordCenter,
           Math.max(boundingBoxBuffer, mineSideLenPx + boundingBoxBuffer),
        ),
      })
    }

    // Magnet mine targeting lines
    for(let i in this._api.frameData.magnet_mine_targeting_lines) {
      let tl = this._api.frameData.magnet_mine_targeting_lines[i]
      let pointA = this.mapCoordToCanvasCoord(
        {x:tl.mine_coord[0], y:tl.mine_coord[1]},
        cameraPosition,
      )
      let pointB = this.mapCoordToCanvasCoord(
        {
          x:tl.target_coord[0] + (getRandomFloat(-30, 30) * this._api.frameData.map_config.units_per_meter / this.getZoom()),
          y:tl.target_coord[1] + (getRandomFloat(-30, 30) * this._api.frameData.map_config.units_per_meter / this.getZoom()),
        },
        cameraPosition,
      )
      drawableItems.magnetMineTargetingLines.push({
        mineCanvasCoord: pointA,
        targetCanvasCoord: pointB,
      })
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

  public getCanvasPointAtLocation(startCanvasCoord: PointCoord, angle: number, canvasDistance: number): PointCoord {
    // Cardinal directions (edge cases)
    if(angle == 0) {
      return {x: startCanvasCoord.x, y: startCanvasCoord.y - canvasDistance}
    } else if (angle == 90) {
      return {x: startCanvasCoord.x + canvasDistance, y: startCanvasCoord.y}
    } else if (angle == 180) {
      return {x: startCanvasCoord.x, y: startCanvasCoord.y + canvasDistance}
    } else if (angle == 270) {
      return {x: startCanvasCoord.x - canvasDistance, y: startCanvasCoord.y}
    }

    // Non cardinal direction
    // Position point canvasDistance above origin, then perform point rotation around origin.
    const ox = startCanvasCoord.x
    const oy = startCanvasCoord.y
    const px = startCanvasCoord.x
    const py = startCanvasCoord.y - canvasDistance
    const ia = angle * -1 * (Math.PI / 180)
    const sia = Math.sin(ia )
    const cia = Math.cos(ia)
    const dx = px - ox
    const dy = py - oy
    const qx = ox + cia * dx - sia * dy
    const qy = oy + sia * dx + cia * dy
    return {
      x: Math.floor(qx),
      y: Math.floor(qy),
    }

  }

}

export const VELOCITY_TRAIL_ELEMENT_TTL_MS = 8000
export class VelocityTrailElement {
  createdAt: number
  radiusMeters: number
  mapCoord: PointCoord
  grow: boolean
}


export const FLAME_SMOKE_ELEMENT_TTL_MS = 3500
export class FlameSmokeElement {
  createdAt: number
  initalRadiusMeters: number
  mapCoord: PointCoord
}


@Injectable({
  providedIn: 'root'
})
export class CameraService {
  // ANGULAR SERVICE * * * *
  // Manages Camera instances


  public gameDisplayCamera: Camera
  public scannerPaneCamera: Camera

  private updateVelocityTrailElementsInterval = 400
  private velocityTrailElements: VelocityTrailElement[] = []

  private updateFlameSmokeElementInterval = 300
  private flameSmokeElements: FlameSmokeElement[] = []

  constructor(
    private _api: ApiService,
  ) {

    this.gameDisplayCamera = new Camera(
      CAMERA_NAME_GAME_DISPLAY,
      this._api,
    )

    this.scannerPaneCamera = new Camera(
      CAMERA_NAME_SCANNER_DISPLAY,
      this._api,
    )

    setTimeout(this.updateVelocityTrailElements.bind(this), this.updateVelocityTrailElementsInterval)
    setTimeout(this.updateFlameSmokeElements.bind(this), this.updateFlameSmokeElementInterval)
  }

  // Flame Smoke
  public getFlameSmokeElements(): FlameSmokeElement[] {
    return this.flameSmokeElements
  }
  private updateFlameSmokeElements() {
    if(!this._api.frameData) {
      console.warn("updateVelocityTrailElements():: no framedata found")
      return setTimeout(this.updateFlameSmokeElements.bind(this), this.updateFlameSmokeElementInterval)
    }
    const now = performance.now()
    // Clear old elements
    this.flameSmokeElements = this.flameSmokeElements.filter((fse: FlameSmokeElement)=>{
      return fse.createdAt + FLAME_SMOKE_ELEMENT_TTL_MS > now
    })
    console.log({smoke: this.flameSmokeElements})
    // Add elements for own ship
    if(this._api.frameData.ship.aflame) {
      this.flameSmokeElements.push({
        createdAt: now,
        mapCoord: {
          x: this._api.frameData.ship.coord_x + getRandomFloat(-7, 7) * this._api.frameData.map_config.units_per_meter,
          y: this._api.frameData.ship.coord_y + getRandomFloat(-7, 7) * this._api.frameData.map_config.units_per_meter,
        },
        initalRadiusMeters: getRandomFloat(4, 7),
      })
    }
    // Add elements from other ships
    for(let i in this._api.frameData.ship.scanner_ship_data){
      let sde = this._api.frameData.ship.scanner_ship_data[i]
      if(sde.aflame) {
        this.flameSmokeElements.push({
          createdAt: now,
          mapCoord: {
            x: sde.coord_x + getRandomFloat(-7, 7) * this._api.frameData.map_config.units_per_meter,
            y: sde.coord_y + getRandomFloat(-7, 7) * this._api.frameData.map_config.units_per_meter,
          },
          initalRadiusMeters: getRandomFloat(4, 7),
        })
      }
    }

    setTimeout(this.updateFlameSmokeElements.bind(this), this.updateFlameSmokeElementInterval)
  }

  // Velocity Visual Dots
  public getVelocityTrailElements(): VelocityTrailElement[] {
    return this.velocityTrailElements
  }
  private updateVelocityTrailElements() {
    if(!this._api.frameData) {
      console.warn("updateVelocityTrailElements():: no framedata found")
      return setTimeout(this.updateVelocityTrailElements.bind(this), this.updateVelocityTrailElementsInterval)
    }

    const now = performance.now()
    // Clear old elements
    this.velocityTrailElements = this.velocityTrailElements.filter((vte: VelocityTrailElement)=>{
      return vte.createdAt + VELOCITY_TRAIL_ELEMENT_TTL_MS > now
    })

    // Add elements for own ship
    if(
      this._api.frameData.ship.velocity_x_meters_per_second
      || this._api.frameData.ship.velocity_y_meters_per_second
    ) {
      this.velocityTrailElements.push({
        createdAt: now,
        mapCoord: {x: this._api.frameData.ship.coord_x, y:this._api.frameData.ship.coord_y},
        radiusMeters: this._api.frameData.ship.engine_lit ? 1.5 : 0.4,
        grow: this._api.frameData.ship.engine_lit,
      })
    }

    // Add elements for scanner elements
    for(let i in this._api.frameData.ship.scanner_ship_data) {
      let sde = this._api.frameData.ship.scanner_ship_data[i]
      if(sde.velocity_x_meters_per_second || sde.velocity_y_meters_per_second){
        this.velocityTrailElements.push({
          createdAt: now,
          mapCoord: {
            x: Math.floor((sde.visual_p0[0] + sde.visual_p3[0]) / 2),
            y: Math.floor((sde.visual_p0[1] + sde.visual_p3[1]) / 2),
          },
          radiusMeters: sde.visual_engine_lit ? 1.5 : 0.4,
          grow: sde.visual_engine_lit,
        })
      }
    }
    for(let i in this._api.frameData.ship.scanner_magnet_mine_data) {
      let sde = this._api.frameData.ship.scanner_magnet_mine_data[i]
      if(!sde.exploded && (sde.velocity_x_meters_per_second || sde.velocity_y_meters_per_second)){
        this.velocityTrailElements.push({
          createdAt: now,
          mapCoord: {x:sde.coord_x, y:sde.coord_y},
          radiusMeters: 1,
          grow: false,
        })
      }
    }

    setTimeout(
      this.updateVelocityTrailElements.bind(this),
      this.updateVelocityTrailElementsInterval,
    )
  }

}
