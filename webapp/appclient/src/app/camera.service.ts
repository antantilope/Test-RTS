
import { Injectable } from '@angular/core';


@Injectable({
  providedIn: 'root'
})
export class CameraService {

  public canvasWidth: number = 0;
  public canvasHeight: number = 0;

  public zoom: number = 1;
  public xPosition: number = null;
  public yPosition: number = null;

  constructor() {

  }

}
