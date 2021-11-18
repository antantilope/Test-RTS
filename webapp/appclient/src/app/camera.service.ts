
import { Injectable } from '@angular/core';

import { ApiService } from './api.service';
import { BoxCoords } from './models/box-coords.model';
import { DrawableObjects } from './models/drawable-objects.model';
import { PointCoord } from './models/point-coord.model';




export const CAMERA_MODE_SHIP = 'ship'
export const CAMERA_MODE_SCANNER = 'scanner'
export const CAMERA_MODE_FREE = 'free'


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
    "Zooming out" increases
  */
  private zoom: number = 1;

  private xPosition: number = null;
  private yPosition: number = null;
  private mode = CAMERA_MODE_SHIP;

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

  public setPosition(x: number, y: number) : void {
    this.xPosition = x
    this.yPosition = y
  }

  public getMode(): string {
    return this.mode;
  }
  public setModeShip(): void {
    this.mode = CAMERA_MODE_SHIP
  }
  public setModeScanner(): void {
    this.mode = CAMERA_MODE_SCANNER
  }
  public setModeFree(): void {
    this.mode = CAMERA_MODE_FREE
  }

  public getCameraBoxCoords(): BoxCoords {
    const x1 = this.xPosition - (this.canvasHalfWidth * this.zoom)
    const y1 = this.yPosition - (this.canvasHalfHeight * this.zoom)
    const x2 = this.xPosition + (this.canvasHalfWidth * this.zoom)
    const y2 = this.yPosition + (this.canvasHalfHeight * this.zoom)
    return {x1, y1, x2, y2}
  }

  public rectCoordsToBoxCoords(
    p0: PointCoord,
    p1: PointCoord,
    p2: PointCoord,
    p3: PointCoord,
  ): BoxCoords {
    return {
      x1: Math.min(p0.x, p1.x, p2.x, p3.x),
      y1: Math.min(p0.y, p1.y, p2.y, p3.y),
      x2: Math.max(p0.x, p1.x, p2.x, p3.x),
      y2: Math.max(p0.y, p1.y, p2.y, p3.y),
    }
  }

  public boxesOverlap(box1: BoxCoords, box2: BoxCoords): boolean {
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

  public getDrawableObjects(): DrawableObjects {
    const drawableObjects: DrawableObjects = {}
    const cameraBoxCoords: BoxCoords = this.getCameraBoxCoords()

    // Ship
    const ship: any = this._api.frameData.ship
    const shipBoxCoords: BoxCoords = this.rectCoordsToBoxCoords(
      ship.rel_rot_coord_0,
      ship.rel_rot_coord_1,
      ship.rel_rot_coord_2,
      ship.rel_rot_coord_3,
    )
    if (this.boxesOverlap(shipBoxCoords, cameraBoxCoords)) {
      drawableObjects.ship = {

      }
    }

    return drawableObjects
  }

}
