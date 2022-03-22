import { Injectable } from '@angular/core';
import { CameraService } from './camera.service';

@Injectable({
  providedIn: 'root'
})
export class PaneService {

  public mouseInPane: boolean = false
  public allChatPaneVisible: boolean = false

  constructor(
    private _camera: CameraService,
  ) { }

  public showChatPane() {
    this.allChatPaneVisible = true
  }
  public hideChatPAne(){
    this.allChatPaneVisible = false
  }
}
