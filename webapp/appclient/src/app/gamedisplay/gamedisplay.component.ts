
import {
  Component,
  OnInit,
  ViewChild,
  ElementRef,
  HostListener,
} from '@angular/core';

import { ApiService } from "../api.service";
import { CameraService } from '../camera.service';


@Component({
  selector: 'app-gamedisplay',
  templateUrl: './gamedisplay.component.html',
  styleUrls: ['./gamedisplay.component.css']
})
export class GamedisplayComponent implements OnInit {

  @ViewChild("graphicsCanvas") canvas: ElementRef;
  @ViewChild("graphicsCanvasContainer") canvasContainer: ElementRef;

  constructor(
    private _api: ApiService,
    private _camera: CameraService,
  ) {
    console.log("gamedisplay::constructor");
  }

  ngOnInit(): void {
    console.log("gamedisplay::ngOnInit");
    this.resizeCanvas();
  }


  // TODO: This is shit. Need a better solution.
  @HostListener('window:resize', ['$event'])
  private handleWindowResize():void {
    location.reload();
  }

  private resizeCanvas() {
    setTimeout(() => {
      this.canvas.nativeElement.width = this.canvas.nativeElement.offsetWidth;
      this.canvas.nativeElement.height = this.canvas.nativeElement.offsetHeight;
    }, 100);
  }

}
