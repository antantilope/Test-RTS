
import {
  Component,
  OnInit,
  ViewChild,
  ElementRef,
  HostListener,
} from '@angular/core'

import {
  DrawableCanvasItems,
  DrawableShip,
} from '../models/drawable-objects.model';
import { ApiService } from "../api.service"
import {
  CameraService,
  CAMERA_MODE_SHIP,
  CAMERA_MODE_SCANNER,
  CAMERA_MODE_FREE,
} from '../camera.service'
import { FormattingService } from '../formatting.service'


@Component({
  selector: 'app-gamedisplay',
  templateUrl: './gamedisplay.component.html',
  styleUrls: ['./gamedisplay.component.css']
})
export class GamedisplayComponent implements OnInit {

  @ViewChild("graphicsCanvas") canvas: ElementRef
  @ViewChild("graphicsCanvasContainer") canvasContainer: ElementRef

  private ctx: any = null

  private isDebug: boolean = false
  private lastFrameTime:any = null
  private clientFPS: number = 0
  private clientFrames: number = 0

  constructor(
    private _api: ApiService,
    private _camera: CameraService,
    private _formatting: FormattingService
  ) {
    console.log("GamedisplayComponent::constructor")
  }

  ngOnInit(): void {
    console.log("GamedisplayComponent::ngOnInit")
  }

  ngAfterViewInit() {
    console.log("GamedisplayComponent::ngAfterViewInit")
    this.isDebug = window.location.search.indexOf("debug") !== -1
    this.resizeCanvas()
    this.setupCanvasContext()
    this.setCanvasColor()
    this.paintDisplay()
  }


  @HostListener('window:resize', ['$event'])
  private handleWindowResize():void {
    location.reload() // TODO: This is shit. Need a better solution.
  }

  private setupCanvasContext(): void {
    this.ctx = this.ctx || this.canvas.nativeElement.getContext("2d")
  }

  private resizeCanvas() {
    setTimeout(() => {
      console.log("resizeCanvas()")
      this.canvas.nativeElement.width = this.canvas.nativeElement.offsetWidth
      this.canvas.nativeElement.height = this.canvas.nativeElement.offsetHeight
      this._camera.setCanvasWidthHeight(
        this.canvas.nativeElement.offsetWidth,
        this.canvas.nativeElement.offsetHeight,
      )
    })
  }

  private setCanvasColor(): void {
    this.canvas.nativeElement.style.backgroundColor = "#000000" // Black
  }

  private paintDisplay(): void {
    this.clearCanvas()
    if(this.isDebug) {
      this.paintDebugData()
    }

    if (this._camera.getMode() === CAMERA_MODE_SHIP) {
      this._camera.setPosition(
        this._api.frameData.ship.coord_x + 150,
        this._api.frameData.ship.coord_y + 150,
      )
    }

    const drawableObjects: DrawableCanvasItems = this._camera.getDrawableCanvasObjects()

    // Ship
    const ship: DrawableShip | undefined = drawableObjects.ship
    if(typeof ship !== "undefined") {
      this.ctx.fillStyle = "#919191"
      this.ctx.beginPath()
      this.ctx.moveTo(ship.canvasCoordP0.x, ship.canvasCoordP0.y)
      this.ctx.lineTo(ship.canvasCoordP1.x, ship.canvasCoordP1.y);
      this.ctx.lineTo(ship.canvasCoordP2.x, ship.canvasCoordP2.y);
      this.ctx.lineTo(ship.canvasCoordP3.x, ship.canvasCoordP3.y);
      this.ctx.closePath()
      this.ctx.fill()
    }

    window.requestAnimationFrame(this.paintDisplay.bind(this))
  }


  private clearCanvas(): void {
    this.ctx.beginPath()
    this.ctx.clearRect(0, 0, this._camera.canvasWidth, this._camera.canvasHeight)
  }


  private paintDebugData(): void {
    /* Draw Debug info on the top right corner of the screen.
    */
    this.ctx.beginPath()
    this.ctx.font = '16px Arial'
    this.ctx.fillStyle = '#ffffff'
    this.ctx.textAlign = 'right'

    const xOffset = this._camera.canvasWidth - 15
    let yOffset = 25
    const yInterval = 20

    const gameFrame = this._formatting.formatNumber(this._api.frameData.game_frame)
    this.ctx.fillText(`frame: ${gameFrame}`, xOffset, yOffset)
    yOffset += yInterval

    this.ctx.fillText(`server FPS: ${this._api.frameData.server_fps}`, xOffset, yOffset)
    yOffset += yInterval

    if(this._api.frameData.server_fps_throttle_seconds) {
      const serverSleep = this._api.frameData.server_fps_throttle_seconds.toFixed(3)
      this.ctx.fillText(`server sleep: ${serverSleep}`, xOffset, yOffset)
      yOffset += yInterval
    }

    this.clientFrames++
    if(this.lastFrameTime === null) {
      this.lastFrameTime = performance.now()
    } else {
      const frameTimeDiffMS = performance.now() - this.lastFrameTime
      this.lastFrameTime = performance.now()
      if(this.clientFrames % 20 === 0) {
        this.clientFPS = (1000 / frameTimeDiffMS)
      }
      this.ctx.fillText(`client FPS: ${this.clientFPS.toFixed()}`, xOffset, yOffset)
      yOffset += yInterval
    }

    const {x, y} = this._camera.getPosition()
    this.ctx.fillText(`camera pos: X: ${x} Y: ${y}`, xOffset, yOffset)
    yOffset += yInterval

    this.ctx.fillText(`camera zoom: ${this._camera.getZoom()}`, xOffset, yOffset)
    yOffset += yInterval

    this.ctx.fillText(`camera mode: ${this._camera.getMode()}`, xOffset, yOffset)
    yOffset += yInterval

    const [shipX, shipY] = [this._api.frameData.ship.coord_x, this._api.frameData.ship.coord_y]
    this.ctx.fillText(`ship pos: X: ${shipX} Y: ${shipY}`, xOffset, yOffset)
    yOffset += yInterval

  }

}
