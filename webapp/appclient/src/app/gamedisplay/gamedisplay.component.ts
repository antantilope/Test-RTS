
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

  private ctx: any = null;

  constructor(
    private _api: ApiService,
    private _camera: CameraService,
  ) {
    console.log("GamedisplayComponent::constructor");
  }

  ngOnInit(): void {
    console.log("GamedisplayComponent::ngOnInit");
  }

  ngAfterViewInit() {
    console.log("GamedisplayComponent::ngAfterViewInit");
    this.setupCanvasContext();
    this.resizeCanvas();
    this.setCanvasColor();
  }


  @HostListener('window:resize', ['$event'])
  private handleWindowResize():void {
    location.reload(); // TODO: This is shit. Need a better solution.
  }

  private resizeCanvas() {
    setTimeout(() => {
      this.canvas.nativeElement.width = this.canvas.nativeElement.offsetWidth;
      this.canvas.nativeElement.height = this.canvas.nativeElement.offsetHeight;
    }, 100);
  }

  private setupCanvasContext(): void {
    this.ctx = this.ctx || this.canvas.nativeElement.getContext("2d");
  }

  private setCanvasColor(): void {
    this.canvas.nativeElement.style.backgroundColor = "#000000" // Black
  }

}
