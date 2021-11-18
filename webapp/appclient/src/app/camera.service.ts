
import { Injectable } from '@angular/core';

import { ApiService } from './api.service';



export const CAMERA_MODE_SHIP = 'ship'
export const CAMERA_MODE_SCANNER = 'scanner'
export const CAMERA_MODE_FREE = 'free'


@Injectable({
  providedIn: 'root'
})
export class CameraService {

  public canvasWidth: number = 0;
  public canvasHeight: number = 0;

  public zoom: number = 1;
  public xPosition: number = null;
  public yPosition: number = null;
  public mode = CAMERA_MODE_SHIP;

  constructor(
    private _api: ApiService,
  ) {
  }

}
