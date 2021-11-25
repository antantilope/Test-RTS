
import {
  Component,
  OnInit,
  ViewChild,
  ElementRef,
  HostListener,
} from '@angular/core'
import { Subscription } from 'rxjs'

import {
  DrawableCanvasItems,
  DrawableShip,
  DrawableReactionWheelOverlay,
  DrawableEngineOverlay,
} from '../models/drawable-objects.model'
import { TimerItem } from '../models/timer-item.model'
import { ApiService } from "../api.service"
import { UserService } from "../user.service"
import {
  CameraService,
  CAMERA_MODE_SHIP,
  CAMERA_MODE_SCANNER,
  CAMERA_MODE_FREE,
} from '../camera.service'
import { FormattingService } from '../formatting.service'
import { PointCoord } from '../models/point-coord.model'



const randomInt = function (min: number, max: number): number  {
  return Math.floor(Math.random() * (max - min) + min)
}



@Component({
  selector: 'app-gamedisplay',
  templateUrl: './gamedisplay.component.html',
  styleUrls: ['./gamedisplay.component.css']
})
export class GamedisplayComponent implements OnInit {

  private frameDataEventSubscription: Subscription


  @ViewChild("graphicsCanvas") canvas: ElementRef
  @ViewChild("graphicsCanvasContainer") canvasContainer: ElementRef

  public enableActivateReactionWheelBtn = false
  public enableEngineOnlineBtn = false
  public enableEngineOfflineBtn = false
  public enableEngineLightBtn = false
  public enableEngineUnLightBtn = false

  private ctx: any | null = null

  /* Props to track the user's mouse */
  private mouseInCanvas = false
  private mouseClickDownInCanvas = false
  private mousePanLastX: number | null = null
  private mousePanLastY: number | null = null
  private mouseMovedWhileDown = false

  /* Props used to hold debug data */
  private isDebug: boolean = false
  private lastFrameTime:any = null
  private clientFPS: number = 0
  private clientFrames: number = 0

  private drawableObjects: DrawableCanvasItems | null = null

  constructor(
    private _api: ApiService,
    public _camera: CameraService,
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

    this.frameDataEventSubscription = this._api.frameDataEvent.subscribe((data: any) => {
      this.refreshButtonStates()
    })
  }

  ngOnDestroy() {
    console.log("GamedisplayComponent::ngOnDestroy")
    this.frameDataEventSubscription.unsubscribe()
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
      this.mouseMovedWhileDown = false
      if(this.mouseInCanvas) {
        this.mouseClickDownInCanvas = true
      }
    })
    window.addEventListener('mouseup', (event) => {
      if(!this.mouseMovedWhileDown && this.mouseInCanvas) {
        this.handleMouseClickInCanvas(event)
      }
      this.mouseClickDownInCanvas = false
      this.mouseMovedWhileDown = false
      this.mousePanLastX = null
      this.mousePanLastY = null

    })
    window.addEventListener('mousemove', event => {
      this.mouseMovedWhileDown = true
      if(!this._camera.canManualPan() || !this.mouseClickDownInCanvas || !this.mouseInCanvas) {
        return
      }
      else if(this.mousePanLastX === null || this.mousePanLastY === null) {
        this.mousePanLastX = event.screenX
        this.mousePanLastY = event.screenY
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

  public handleMouseClickInCanvas(event: any): void {
    console.log("handleMouseClickInCanvas")
    if(this._api.frameData === null) {
      return
    }
    const mouseCanvasX = event.clientX - this.canvas.nativeElement.offsetLeft
    const mouseCanvasY = event.clientY - this.canvas.nativeElement.offsetTop
    if(
      this._api.frameData.ship.reaction_wheel_online
      && !this._api.frameData.ship.autopilot_online
      && this.drawableObjects !== null
      && typeof this.drawableObjects.ships[0] !== 'undefined'
      && this.drawableObjects.ships[0].isSelf
    ) {
      this.handleMouseClickInCanvasHeadingAdjust(mouseCanvasX, mouseCanvasY)
    }
  }

  private async handleMouseClickInCanvasHeadingAdjust(canvasClickX: number, canvasClickY: number) {
    const canvasClickPoint: PointCoord = {x: canvasClickX, y: canvasClickY}
    const canvasShipPoint: PointCoord = this.drawableObjects.ships[0].canvasCoordCenter
    const heading = this._camera.getCanvasAngleBetween(canvasShipPoint, canvasClickPoint)
    console.log({set_heading: heading})
    await this._api.post(
      "/api/rooms/command",
      {command: "set_heading", heading},
    )
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
    this.drawableObjects = drawableObjects

    // draw visual ships and scanned ships
    for(let i in drawableObjects.ships) {
      const drawableShip: DrawableShip = drawableObjects.ships[i]
      if(drawableShip.canvasCoordP0) {
        this.ctx.beginPath()
        this.ctx.fillStyle = drawableShip.fillColor
        this.ctx.moveTo(drawableShip.canvasCoordP0.x, drawableShip.canvasCoordP0.y)
        this.ctx.lineTo(drawableShip.canvasCoordP1.x, drawableShip.canvasCoordP1.y)
        this.ctx.lineTo(drawableShip.canvasCoordP2.x, drawableShip.canvasCoordP2.y)
        this.ctx.lineTo(drawableShip.canvasCoordP3.x, drawableShip.canvasCoordP3.y)
        this.ctx.closePath()
        this.ctx.fill()

        if (drawableShip.isSelf) {
          const visibleRangeCanvasPXRadius = Math.round(
            (this._api.frameData.map_config.units_per_meter
            * this._api.frameData.ship.visual_range) / this._camera.getZoom()
          )
          this.ctx.beginPath()
          this.ctx.strokeStyle = "#808080"
          this.ctx.lineWidth = 1
          this.ctx.arc(
            drawableShip.canvasCoordCenter.x,
            drawableShip.canvasCoordCenter.y,
            visibleRangeCanvasPXRadius,
            0,
            2 * Math.PI,
          )
          this.ctx.stroke()
        }

        if(drawableShip.engineLit) {
          const engineFlameX = Math.round((drawableShip.canvasCoordP3.x + drawableShip.canvasCoordP0.x) / 2)
          const engineFlameY = Math.round((drawableShip.canvasCoordP3.y + drawableShip.canvasCoordP0.y) / 2)
          let engineOuterFlameRadius = Math.max(4, Math.round(
            Math.sqrt(
              (Math.pow(drawableShip.canvasCoordP3.x - drawableShip.canvasCoordP0.x, 2)
              + Math.pow(drawableShip.canvasCoordP3.y - drawableShip.canvasCoordP0.y, 2))
            ) / 2
          ))
          engineOuterFlameRadius += randomInt(engineOuterFlameRadius / 4, engineOuterFlameRadius)
          this.ctx.beginPath()
          this.ctx.fillStyle = "rgb(255, 0, 0, 0.9)"
          this.ctx.arc(
            engineFlameX,
            engineFlameY,
            engineOuterFlameRadius,
            0,
            2 * Math.PI,
          )
          this.ctx.fill()
          this.ctx.beginPath()
          this.ctx.fillStyle = "rgb(255, 186, 89, 0.8)"
          const engineInnerFlameRadius = Math.floor(engineOuterFlameRadius / 2) + randomInt(
            engineOuterFlameRadius / -5, engineOuterFlameRadius / 5
          )
          this.ctx.arc(
            engineFlameX + randomInt(engineInnerFlameRadius / -4, engineInnerFlameRadius / 4),
            engineFlameY+ randomInt(engineInnerFlameRadius / -4, engineInnerFlameRadius / 4),
            engineInnerFlameRadius,
            0,
            2 * Math.PI,
          )
          this.ctx.fill()
        }
      }
    }

    // Reaction Wheel overlay
    const reactionWheelOverlay: DrawableReactionWheelOverlay | undefined = drawableObjects.reactionWheelOverlay
    if(typeof reactionWheelOverlay !== "undefined") {
      this.ctx.beginPath()
      this.ctx.strokeStyle = "rgb(43, 255, 0, 0.6)"
      this.ctx.lineWidth = 1
      this.ctx.arc(
        reactionWheelOverlay.centerCanvasCoord.x,
        reactionWheelOverlay.centerCanvasCoord.y,
        reactionWheelOverlay.radiusPx,
        0,
        2 * Math.PI);
      this.ctx.stroke();

      this.ctx.beginPath()
      this.ctx.moveTo(reactionWheelOverlay.compassPoint0.x, reactionWheelOverlay.compassPoint0.y)
      this.ctx.lineTo(reactionWheelOverlay.compassPoint1.x, reactionWheelOverlay.compassPoint1.y)
      this.ctx.stroke();
      this.ctx.beginPath()
      this.ctx.font = 'bold 18px Courier New'
      this.ctx.fillStyle = 'rgb(43, 255, 0,  0.8)'
      this.ctx.textAlign = 'center'
      this.ctx.fillText(
        this._api.frameData.ship.heading,
        reactionWheelOverlay.compassPoint1.x,
        reactionWheelOverlay.compassPoint1.y,
      )
    }

    // Engine overlay
    const engineOverlay: DrawableEngineOverlay | undefined = drawableObjects.engineOverlay
    if(typeof engineOverlay !== "undefined") {
      this.ctx.beginPath()
      this.ctx.strokeStyle = "rgb(255, 0, 0, 0.6)"
      this.ctx.lineWidth = 2
      this.ctx.moveTo(engineOverlay.vectorPoint0.x, engineOverlay.vectorPoint0.y)
      this.ctx.lineTo(engineOverlay.vectorPoint1.x, engineOverlay.vectorPoint1.y)
      this.ctx.stroke();
      this.ctx.beginPath()
      this.ctx.font = 'bold 18px Courier New'
      this.ctx.fillStyle = 'rgb(255, 0, 0,  0.8)'
      this.ctx.textAlign = 'center'
      this.ctx.fillText(
        engineOverlay.metersPerSecond + " M/S",
        engineOverlay.vectorPoint1.x,
        engineOverlay.vectorPoint1.y,
      )
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
    let scaleLabel;
    if(barLengthMeters >= 5000) {
      scaleLabel = (barLengthMeters / 1000).toFixed(2) + " KM"
    }
    else {
      scaleLabel = Math.round(barLengthMeters) + " Meters"
    }
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
    this.ctx.fillText(scaleLabel, lrcXOffset + 8, lrcYOffset - 12)
    lrcYOffset -= lrcYInterval
    this.ctx.beginPath()
    this.ctx.font = '20px Courier New'
    this.ctx.fillText("Ensign " + this._user.handle, lrcXOffset, lrcYOffset)
    lrcYOffset -= lrcYInterval

    // Resources (TOP LEFT)
    const tlcYInterval = 34
    let tlcYOffset = 25
    const tlcXOffset = 15
    this.ctx.beginPath()
    this.ctx.font = '24px Courier New'
    this.ctx.fillStyle = '#fcb8b8'
    this.ctx.textAlign = 'left'
    this.ctx.fillText("⛽ " + this._formatting.formatNumber(this._api.frameData.ship.fuel_level), tlcXOffset, tlcYOffset)
    tlcYOffset += tlcYInterval

    this.ctx.beginPath()
    this.ctx.fillStyle = '#fcf9b8'
    this.ctx.textAlign = 'left'
    this.ctx.fillText("🔋 " + this._formatting.formatNumber(this._api.frameData.ship.battery_power), tlcXOffset, tlcYOffset)
    tlcYOffset += tlcYInterval

    // Timers (BOTTOM RIGHT)
    const brcYInterval = 45
    let brcYOffset = 30
    const brcXOffset = 15
    const timerBarLength = Math.round(this._camera.canvasWidth / 8)
    const textRAlignXOffset = brcXOffset + timerBarLength + 10
    const barRAlignXOffset = brcXOffset + timerBarLength

    this.ctx.strokeStyle = '#ffffff'
    this.ctx.fillStyle = '#ffffff'
    this.ctx.lineWidth = 1
    this.ctx.textAlign = 'right'
    this.ctx.font = 'bold 24px Courier New'
    this.ctx.beginPath()
    this.ctx.fillText(
      this._api.frameData.elapsed_time,
      this._camera.canvasWidth - 15,
      this._camera.canvasHeight - brcYOffset,
    )
    this.ctx.font = '20px Courier New'
    this.ctx.strokeStyle = '#00ff00'
    this.ctx.fillStyle = '#00ff00'
    brcYOffset += brcYInterval
    for(let i in this._api.frameData.ship.timers) {
      const timer: TimerItem = this._api.frameData.ship.timers[i]
      const fillLength = Math.round((timer.percent / 100) * timerBarLength)
      this.ctx.beginPath()
      this.ctx.fillText(
        timer.name,
        this._camera.canvasWidth - textRAlignXOffset,
        this._camera.canvasHeight - brcYOffset,
      )
      this.ctx.beginPath()
      this.ctx.rect(
        this._camera.canvasWidth - barRAlignXOffset, //    top left x
        this._camera.canvasHeight - (brcYOffset + 20),  // top left y
        timerBarLength, // width
        30,             // height
      )
      this.ctx.stroke()
      this.ctx.beginPath()
      this.ctx.rect(
        this._camera.canvasWidth - barRAlignXOffset, //    top left x
        this._camera.canvasHeight - (brcYOffset + 20),  // top left y
        fillLength, // width
        30,         // height
      )
      this.ctx.fill()

      brcYOffset += brcYInterval

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

    const [shipVelX, shipVelY] = [
      this._api.frameData.ship.velocity_x_meters_per_second,
      this._api.frameData.ship.velocity_y_meters_per_second,
    ]
    this.ctx.fillText(`ship Velocity: X: ${shipVelX.toFixed(2)} Y: ${shipVelY.toFixed(2)}`, xOffset, yOffset)
    yOffset += yInterval

  }


  public async refreshButtonStates() {
    if(this._api.frameData === null) {
      return
    }
    if(this._api.frameData.ship.available_commands.includes('activate_reaction_wheel')) {
      this.enableActivateReactionWheelBtn = true
    }
    else {
      this.enableActivateReactionWheelBtn = false
    }

    this.enableEngineOnlineBtn = this._api.frameData.ship.available_commands.includes('activate_engine')
    this.enableEngineOfflineBtn = this._api.frameData.ship.available_commands.includes('deactivate_engine')
    this.enableEngineLightBtn = this._api.frameData.ship.available_commands.includes('light_engine')
    this.enableEngineUnLightBtn = this._api.frameData.ship.available_commands.includes('unlight_engine')

  }


  public async btnActivateReactionWheel() {
    if(!this.enableActivateReactionWheelBtn) {
      return
    }
    console.log("btnActivateReactionWheel()")
    await this._api.post(
      "/api/rooms/command",
      {command:'activate_reaction_wheel'},
    )
  }

  public async btnDeactivateReactionWheel() {
    if(this.enableActivateReactionWheelBtn) {
      return
    }
    console.log("btnDeactivateReactionWheel()")
    await this._api.post(
      "/api/rooms/command",
      {command:'deactivate_reaction_wheel'},
    )
  }

  public async btnActivateEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'activate_engine'},
    )
  }

  public async btnDeactivateEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'deactivate_engine'},
    )
  }

  public async btnLightEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'light_engine'},
    )
  }

  public async btnUnlightEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'unlight_engine'},
    )
  }

}
