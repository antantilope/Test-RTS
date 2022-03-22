import { Injectable } from '@angular/core';
import { CameraService } from './camera.service';

@Injectable({
  providedIn: 'root'
})
export class PaneService {

  public mouseInPane: boolean = false
  public showChatPane: boolean = false

  constructor(
    private _camera: CameraService,
  ) { }


}
