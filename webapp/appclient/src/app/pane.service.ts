import { Injectable } from '@angular/core';
import { CameraService } from './camera.service';

@Injectable({
  providedIn: 'root'
})
export class PaneService {

  public mouseInPane: boolean = false
  public showScannerPane: boolean = false

  constructor(
    private _camera: CameraService,
  ) { }


  public openScannerPane():void {
    this.showScannerPane = true
    this._camera.setModeScanner()
  }

  public closeScannerPane():void {
    this.showScannerPane = false
    this.mouseInPane = false
    this._camera.setModeShip()
  }

}
