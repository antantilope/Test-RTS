
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
} from '../models/drawable-objects.model'
import { ApiService } from "../api.service"
import { UserService } from "../user.service"
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

  private ctx: any | null = null

  /* Props to track the user's mouse */
  private mouseInCanvas = false
  private mouseClickDownInCanvas = false
  private mousePanLastX: number | null = null
  private mousePanLastY: number | null = null

  /* Props used to hold debug data */
  private isDebug: boolean = false
  private lastFrameTime:any = null
  private clientFPS: number = 0
  private clientFrames: number = 0

  constructor(
    private _api: ApiService,
    private _camera: CameraService,
    private _formatting: FormattingService,
    public _user: UserService,
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

    this.registerMouseEventListener()
  }


  @HostListener('window:resize', ['$event'])
  private handleWindowResize():void {
    location.reload() // TODO: This is shit. Need a better solution.
  }

  private registerMouseEventListener(): void {
    // Zoom camera
    window.addEventListener('wheel', event => {
      if (this._camera.canManualZoom()) {
        const zoomIn = event.deltaY < 0
        this._camera.adjustZoom(zoomIn)
      }
    })

    // Pan camera
    this.canvas.nativeElement.addEventListener('mouseenter', ()=>{
      this.mouseInCanvas = true
    })
    this.canvas.nativeElement.addEventListener('mouseleave', event => {
      const canvasWidth = this.canvas.nativeElement.width
      const canvasHeight = this.canvas.nativeElement.height
      const eventXPos = event.clientX
      const eventYPos = event.clientY
      if (eventYPos < 0 || eventYPos > canvasHeight || eventXPos < 0 || eventXPos > canvasWidth) {
        this.mouseClickDownInCanvas = false
        this.mouseInCanvas = false
        this.mousePanLastX = null
        this.mousePanLastY = null
      }
    })
    this.canvas.nativeElement.addEventListener('mousedown', ()=>{
      if(this.mouseInCanvas) {
        this.mouseClickDownInCanvas = true
      }
    })
    window.addEventListener('mouseup', ()=>{
      this.mouseClickDownInCanvas = false
      this.mousePanLastX = null
      this.mousePanLastY = null
    })
    window.addEventListener('mousemove', event => {
      if(!this._camera.canManualPan() || !this.mouseClickDownInCanvas || !this.mouseInCanvas) {
        return
      }
      else if(this.mousePanLastX === null || this.mousePanLastY === null) {
        this.mousePanLastX = event.screenX
        this.mousePanLastY = event.screenY
        return
      }
      else {
        const cameraZoom = this._camera.getZoom()
        const scaledDeltaX = (this.mousePanLastX - event.screenX) * cameraZoom
        const scaledDeltaY = (this.mousePanLastY - event.screenY) * cameraZoom * -1
        this._camera.xPan(scaledDeltaX)
        this._camera.yPan(scaledDeltaY)
        this.mousePanLastX = event.screenX
        this.mousePanLastY = event.screenY
      }
    })
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

    if (this._api.frameData === null) {
      window.requestAnimationFrame(this.paintDisplay.bind(this))
      return
    }

    const camCoords = this._camera.getPosition()
    const camMode = this._camera.getMode()
    if(camCoords.x === null || camCoords.y === null) {
      this._api.frameData
      this._camera.setPosition(
        this._api.frameData.ship.coord_x,
        this._api.frameData.ship.coord_y,
      )
    }

    this.clearCanvas()
    if(this.isDebug) {
      this.paintDebugData()
    }

    if (camMode === CAMERA_MODE_SHIP) {
      this._camera.setPosition(
        this._api.frameData.ship.coord_x,
        this._api.frameData.ship.coord_y,
      )
    }

    const drawableObjects: DrawableCanvasItems = this._camera.getDrawableCanvasObjects()

    // Ship
    const ship: DrawableShip | undefined = drawableObjects.ship
    if(typeof ship !== "undefined") {
      this.ctx.fillStyle = "#919191"
      this.ctx.beginPath()
      this.ctx.moveTo(ship.canvasCoordP0.x, ship.canvasCoordP0.y)
      this.ctx.lineTo(ship.canvasCoordP1.x, ship.canvasCoordP1.y)
      this.ctx.lineTo(ship.canvasCoordP2.x, ship.canvasCoordP2.y)
      this.ctx.lineTo(ship.canvasCoordP3.x, ship.canvasCoordP3.y)
      this.ctx.closePath()
      this.ctx.fill()
    }


    // lower right corner
    let lrcYOffset = this._camera.canvasHeight - 30
    const lrcYInterval = 40
    const lrcXOffset = 15
    // Scale Bar
    const barLengthMeters = (
      (
        (this._camera.canvasWidth / 4)
        * this._camera.getZoom()
      )
      / this._api.frameData.map_config.units_per_meter
    )
    this.ctx.beginPath()
    this.ctx.strokeStyle = "#ffffff"
    this.ctx.lineWidth = 3
    this.ctx.moveTo(lrcXOffset, lrcYOffset);
    this.ctx.lineTo((this._camera.canvasWidth / 4) + lrcXOffset, lrcYOffset);
    this.ctx.stroke()
    this.ctx.beginPath()
    this.ctx.moveTo(lrcXOffset, lrcYOffset);
    this.ctx.lineTo( lrcXOffset, lrcYOffset - 10);
    this.ctx.stroke()
    this.ctx.beginPath()
    this.ctx.moveTo((this._camera.canvasWidth / 4) + lrcXOffset, lrcYOffset);
    this.ctx.lineTo((this._camera.canvasWidth / 4) + lrcXOffset, lrcYOffset - 10);
    this.ctx.stroke()
    // Scale meters and user handle
    this.ctx.beginPath()
    this.ctx.font = '24px serif'
    this.ctx.fillStyle = '#ffffff'
    this.ctx.textAlign = 'left'
    this.ctx.fillText(Math.round(barLengthMeters) + " Meters", lrcXOffset + 8, lrcYOffset - 12)
    lrcYOffset -= lrcYInterval
    this.ctx.beginPath()
    this.ctx.font = '20px Courier New'
    this.ctx.fillText("Ensign " + this._user.handle, lrcXOffset, lrcYOffset)
    lrcYOffset -= lrcYInterval

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
