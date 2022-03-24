
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
import { TimerItem } from '../models/timer-item.model'
import { ApiService } from "../api.service"
import { UserService } from "../user.service"
import { PaneService } from '../pane.service'
import { QuoteService, QuoteDetails } from '../quote.service'
import {
  CameraService,
  CAMERA_MODE_SHIP,
  CAMERA_MODE_SCANNER,
  CAMERA_MODE_FREE,
} from '../camera.service'
import { FormattingService } from '../formatting.service'
import { AllchatService } from "../allchat.service"
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


  @ViewChild("graphicsCanvas") canvas: ElementRef
  @ViewChild("graphicsCanvasContainer") canvasContainer: ElementRef
  @ViewChild("sidebarElement") sidebarElement: ElementRef

  public scannerTargetIDCursor: string | null = null


  private ctx: any | null = null

  /* Props to track the user's mouse */
  private mouseInCanvas = false
  private mouseClickDownInCanvas = false
  private mousePanLastX: number | null = null
  private mousePanLastY: number | null = null
  private mouseMovedWhileDown = false

  /* Props to track click to change heading feedback */
  private clickAnimationFrame: number | null = null
  private clickAnimationCanvasX: number | null = null
  private clickAnimationCanvasY: number | null = null

  /* Props used to hold debug data */
  private isDebug: boolean = false
  private lastFrameTime:any = null
  private clientFPS: number = 0
  private clientFrames: number = 0

  private drawableObjects: DrawableCanvasItems | null = null

  private deathQuote: QuoteDetails | null = null;

  constructor(
    public _api: ApiService,
    public _camera: CameraService,
    private _formatting: FormattingService,
    public _user: UserService,
    public _pane: PaneService,
    public _allchat: AllchatService,
    private _quote: QuoteService,
  ) {
    console.log("GamedisplayComponent::constructor")
  }

  ngOnInit(): void {
    console.log("GamedisplayComponent::ngOnInit")
    this.deathQuote = this._quote.getQuote()
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

  ngOnDestroy() {
    console.log("GamedisplayComponent::ngOnDestroy")
  }


  @HostListener('window:resize', ['$event'])
  private handleWindowResize():void {
    location.reload() // TODO: This is shit. Need a better solution.
  }

  private registerMouseEventListener(): void {
    // Zoom camera
    window.addEventListener('wheel', event => {
      if(this._pane.mouseInPane()) {
        return
      }
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
      if (
        eventYPos < 0
        || eventYPos > canvasHeight
        || eventXPos < 0
        || eventXPos > canvasWidth
        || eventXPos < this.sidebarElement.nativeElement.offsetWidth
      ) {
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
      if(!this.mouseMovedWhileDown && this.mouseInCanvas && !this._pane.mouseInPane()) {
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
      !this._api.frameData.ship.autopilot_program
      && this.drawableObjects !== null
      && typeof this.drawableObjects.ships[0] !== 'undefined'
      && this.drawableObjects.ships[0].isSelf
    ) {
      this.clickAnimationFrame = 1
      this.clickAnimationCanvasX = mouseCanvasX
      this.clickAnimationCanvasY = mouseCanvasY

      this.handleMouseClickInCanvasHeadingAdjust(mouseCanvasX, mouseCanvasY)
    }
  }

  private async handleMouseClickInCanvasHeadingAdjust(canvasClickX: number, canvasClickY: number) {
    const canvasClickPoint: PointCoord = {x: canvasClickX, y: canvasClickY}
    if(!this.drawableObjects.ships[0].isSelf) {
      return console.warn("could not handle heading adjust. ship0 != self")
    }
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
    else if (camMode === CAMERA_MODE_SCANNER) {
      this._camera.setCameraPositionAndZoomForScannerMode(
        this.scannerTargetIDCursor,
      )
    }

    const drawableObjects: DrawableCanvasItems = this._camera.getDrawableCanvasObjects()
    this.drawableObjects = drawableObjects

    // Vision circles
    for(let i in drawableObjects.visionCircles) {
      let vs = drawableObjects.visionCircles[i]
      this.ctx.beginPath()
      this.ctx.fillStyle = vs.color
      this.ctx.arc(
        vs.canvasCoord.x,
        vs.canvasCoord.y,
        vs.radius,
        0,
        2 * Math.PI,
      )
      this.ctx.fill()
    }

    // Draw Map boundary
    this.ctx.beginPath()
    this.ctx.strokeStyle ="#636300"
    this.ctx.lineWidth = Math.max(1, 500 / this._camera.getZoom())
    this.ctx.rect(
      drawableObjects.mapWall.x1,
      drawableObjects.mapWall.y1,
      drawableObjects.mapWall.x2 - drawableObjects.mapWall.x1,
      drawableObjects.mapWall.y2 - drawableObjects.mapWall.y1,
    )
    this.ctx.stroke()

    // draw ships
    for(let i in drawableObjects.ships) {
      const drawableShip: DrawableShip = drawableObjects.ships[i]

      if (drawableShip.isDot) {
        this.ctx.beginPath()
        this.ctx.fillStyle = "rgb(0, 255, 0, 0.9)"
        this.ctx.arc(
          drawableShip.canvasCoordCenter.x,
          drawableShip.canvasCoordCenter.y,
          this._camera.minSizeForDotPx - 1,
          0,
          2 * Math.PI,
        )
        this.ctx.fill()
      }

      if(drawableShip.isVisual && !drawableShip.explosionFrame) {
        // Ship is within visual range
        this.ctx.beginPath()
        this.ctx.fillStyle = drawableShip.fillColor
        this.ctx.moveTo(drawableShip.canvasCoordP0.x, drawableShip.canvasCoordP0.y)
        this.ctx.lineTo(drawableShip.canvasCoordP1.x, drawableShip.canvasCoordP1.y)
        this.ctx.lineTo(drawableShip.canvasCoordP2.x, drawableShip.canvasCoordP2.y)
        this.ctx.lineTo(drawableShip.canvasCoordP3.x, drawableShip.canvasCoordP3.y)
        this.ctx.closePath()
        this.ctx.fill()


        // fin 0
        this.ctx.beginPath()
        this.ctx.moveTo(drawableShip.canvasCoordP0.x, drawableShip.canvasCoordP0.y)
        this.ctx.lineTo(drawableShip.canvasCoordFin0P0.x, drawableShip.canvasCoordFin0P0.y)
        this.ctx.lineTo(drawableShip.canvasCoordFin0P1.x, drawableShip.canvasCoordFin0P1.y)
        this.ctx.closePath()
        this.ctx.fill()
        // fin 1
        this.ctx.beginPath()
        this.ctx.moveTo(drawableShip.canvasCoordP3.x, drawableShip.canvasCoordP3.y)
        this.ctx.lineTo(drawableShip.canvasCoordFin1P0.x, drawableShip.canvasCoordFin1P0.y)
        this.ctx.lineTo(drawableShip.canvasCoordFin1P1.x, drawableShip.canvasCoordFin1P1.y)
        this.ctx.closePath()
        this.ctx.fill()

        if(drawableShip.engineLit) {
          const engineFlameX = Math.round((drawableShip.canvasCoordP3.x + drawableShip.canvasCoordP0.x) / 2)
          const engineFlameY = Math.round((drawableShip.canvasCoordP3.y + drawableShip.canvasCoordP0.y) / 2)
          let engineOuterFlameRadius = Math.max(2, Math.round(
            Math.sqrt(
              (Math.pow(drawableShip.canvasCoordP3.x - drawableShip.canvasCoordP0.x, 2)
              + Math.pow(drawableShip.canvasCoordP3.y - drawableShip.canvasCoordP0.y, 2))
            ) / 2
          ) * (drawableShip.engineBoosted ? 4 : 1))
          engineOuterFlameRadius += randomInt(engineOuterFlameRadius / 4, engineOuterFlameRadius)
          this.ctx.beginPath()
          this.ctx.fillStyle = drawableShip.engineBoosted ? "rgb(71, 139, 255)" : "rgb(255, 0, 0, 0.9)"
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
            engineFlameY + randomInt(engineInnerFlameRadius / -4, engineInnerFlameRadius / 4),
            engineInnerFlameRadius,
            0,
            2 * Math.PI,
          )
          this.ctx.fill()
        }
      }

      if(drawableShip.aflame) {
        const flameRadius = Math.max(4, Math.round(
          Math.sqrt(
            (Math.pow(drawableShip.canvasCoordP1.x - drawableShip.canvasCoordP0.x, 2)
            + Math.pow(drawableShip.canvasCoordP1.y - drawableShip.canvasCoordP0.y, 2))
          ) / 4
        ))
        for(let i=0; i<2; i++) {
          let tFlameRadius = flameRadius + randomInt(flameRadius / 4, flameRadius * 4)
          this.ctx.beginPath()
          this.ctx.fillStyle = `rgb(255, 0, 0, 0.${randomInt(2, 7)})`
          this.ctx.arc(
            drawableShip.canvasCoordCenter.x + randomInt(-5, 5),
            drawableShip.canvasCoordCenter.y + randomInt(-5, 5),
            tFlameRadius,
            0,
            2 * Math.PI,
          )
          this.ctx.fill()
        }
        const sparkCount = randomInt(0, 4)
        const sparkSize = Math.max(5, flameRadius)
        for(let i=0; i<sparkCount; i++) {
          let sparkAngle = randomInt(0, 359)
          let sparkDistance = flameRadius * randomInt(1, 3)
          let sparkPoint = this._camera.getCanvasPointAtLocation(
            drawableShip.canvasCoordCenter,
            sparkAngle,
            sparkDistance
          )
          this.ctx.beginPath()
          this.ctx.fillStyle = 'rgb(255, 0, 0, 1)'
          this.ctx.arc(
            sparkPoint.x,
            sparkPoint.y,
            sparkSize,
            0,
            2 * Math.PI,
          )
          this.ctx.fill()
        }
      }
      if(drawableShip.explosionFrame && drawableShip.explosionFrame < 150) {
        /* Explosion schedule
          frame 1-6 fireball growth
          frame 7-75 pulsating fireball
          frame 76-150 fading smoke puff
        */
        let maxFireBallRadius = Math.round(
          Math.sqrt(
            (Math.pow(drawableShip.canvasCoordP1.x - drawableShip.canvasCoordP0.x, 2)
            + Math.pow(drawableShip.canvasCoordP1.y - drawableShip.canvasCoordP0.y, 2))
          ) * 10
        )
        if(drawableShip.explosionFrame < 8) {
          let fbSize = (drawableShip.explosionFrame / 7) * maxFireBallRadius
          this.ctx.beginPath()
          this.ctx.fillStyle = 'rgb(255, 0, 0, 1)'
          this.ctx.arc(
            drawableShip.canvasCoordCenter.x + randomInt(-3, 3),
            drawableShip.canvasCoordCenter.y + randomInt(-3, 3),
            fbSize,
            0,
            2 * Math.PI,
          )
          this.ctx.fill()
        } else if (drawableShip.explosionFrame < 76) {
          // Main fireball
          let fbSize = maxFireBallRadius * (randomInt(5, 8) / 7)
          this.ctx.beginPath()
          this.ctx.fillStyle = `rgb(255, 0, 0, 0.${randomInt(5, 9)})`
          this.ctx.arc(
            drawableShip.canvasCoordCenter.x + randomInt(-3, 3),
            drawableShip.canvasCoordCenter.y + randomInt(-3, 3),
            fbSize,
            0,
            2 * Math.PI,
          )
          this.ctx.fill()
          // Inner sub fireballs
          const subFireBallsCount = randomInt(2, 4)
          for(let i=0; i<subFireBallsCount; i++) {
            let subFBSize = Math.floor(fbSize / randomInt(2, 4))
            this.ctx.beginPath()
            this.ctx.fillStyle = `rgb(255, ${randomInt(20, 65)}, 0, 0.${randomInt(7, 9)})`
            this.ctx.arc(
              drawableShip.canvasCoordCenter.x + randomInt(-8, 8),
              drawableShip.canvasCoordCenter.y + randomInt(-8, 8),
              subFBSize,
              0,
              2 * Math.PI,
            )
            this.ctx.fill()
          }
          // Deris Lines
          const debrisLineCount = randomInt(-6, 3)
          for(let i=0; i<debrisLineCount; i++) {
            let lineLength = maxFireBallRadius * randomInt(2, 4)
            let angle = randomInt(0, 359)
            let linep1 = this._camera.getCanvasPointAtLocation(
              drawableShip.canvasCoordCenter,
              angle,
              randomInt(0, 50),
            )
            let linep2 = this._camera.getCanvasPointAtLocation(
              drawableShip.canvasCoordCenter,
              angle,
              lineLength,
            )
            this.ctx.beginPath()
            this.ctx.strokeStyle = "rgb(255, 220, 220, 0.90)"
            this.ctx.moveTo(linep1.x, linep1.y)
            this.ctx.lineTo(linep2.x, linep2.y)
            this.ctx.stroke()
          }
        } else {
          let smokePuffSize = Math.floor(maxFireBallRadius / 1.1);
          let alpha = (1 - ((drawableShip.explosionFrame - 76) / 75)) / 3
          this.ctx.beginPath()
          this.ctx.fillStyle = `rgb(255, 130, 130, ${alpha})`
          this.ctx.arc(
            drawableShip.canvasCoordCenter.x,
            drawableShip.canvasCoordCenter.y,
            smokePuffSize,
            0,
            2 * Math.PI,
          )
          this.ctx.fill()
        }
      }

      if(drawableShip.canvasBoundingBox && !drawableShip.explosionFrame) {
        const shipIsLocked = this._api.frameData.ship.scanner_locked && drawableShip.shipId === this._api.frameData.ship.scanner_lock_target
        const shipIsLockedOrLocking = drawableShip.shipId === this._api.frameData.ship.scanner_lock_target && (
          this._api.frameData.ship.scanner_locked || this._api.frameData.ship.scanner_locking
        )
        const cursorOnShip = drawableShip.shipId === this.scannerTargetIDCursor
        this.ctx.beginPath()
        this.ctx.strokeStyle = drawableShip.isSelf ? "rgb(200, 200, 200, 0.85)" : "rgb(255, 0, 0, 0.85)"
        this.ctx.lineWidth = 2.5
        this.ctx.rect(
          drawableShip.canvasBoundingBox.x1,
          drawableShip.canvasBoundingBox.y1,
          drawableShip.canvasBoundingBox.x2 - drawableShip.canvasBoundingBox.x1,
          drawableShip.canvasBoundingBox.y2 - drawableShip.canvasBoundingBox.y1,
        )
        this.ctx.stroke()

        const bbXOffset = drawableShip.canvasBoundingBox.x1
        let bbYOffset = drawableShip.canvasBoundingBox.y2 + 20
        const bbYInterval = 20
        this.ctx.beginPath()
        this.ctx.font = 'bold 18px Courier New'
        this.ctx.fillStyle = drawableShip.isSelf ? "rgb(200, 200, 200, 0.85)" : "rgb(255, 0, 0, 0.85)"
        this.ctx.textAlign = 'left'
        let desigPrefix = cursorOnShip ? "👉" : ""
        if(!drawableShip.alive) {
          desigPrefix = desigPrefix + "💀"
        }
        this.ctx.fillText(desigPrefix + drawableShip.designator, bbXOffset, bbYOffset)
        bbYOffset += bbYInterval
        if(drawableShip.distance) {
          this.ctx.beginPath()
          this.ctx.fillText(drawableShip.distance + " M", bbXOffset, bbYOffset)
          bbYOffset += bbYInterval
        }
        if(drawableShip.thermalSignature) {
          this.ctx.beginPath()
          this.ctx.fillText(
            drawableShip.thermalSignature + ` / ${this._api.frameData.ship.scanner_ir_minimum_thermal_signature} IR`,
            bbXOffset,
            bbYOffset,
          )
          bbYOffset += bbYInterval
        }
        if (shipIsLockedOrLocking && this._api.frameData.ship.scanner_lock_traversal_slack !== null) {
          const midX  = (drawableShip.canvasBoundingBox.x2 + drawableShip.canvasBoundingBox.x1) / 2
          const midY  = (drawableShip.canvasBoundingBox.y2 + drawableShip.canvasBoundingBox.y1) / 2
          const dx = drawableShip.canvasBoundingBox.x2 - drawableShip.canvasBoundingBox.x1
          const dy = drawableShip.canvasBoundingBox.y2 - drawableShip.canvasBoundingBox.y1
          const maxRadius = Math.max(dx, dy)
          const distance = maxRadius * this._api.frameData.ship.scanner_lock_traversal_slack
          // Vertical CH
          this.ctx.beginPath()
          this.ctx.strokeStyle = this._api.frameData.ship.scanner_locked ? "rgb(255, 0, 0, 0.85)" : "rgb(255, 0, 0, 0.5)"
          this.ctx.moveTo(midX + distance, midY + maxRadius)
          this.ctx.lineTo(midX + distance, midY - maxRadius)
          this.ctx.stroke()
          this.ctx.beginPath()
          this.ctx.moveTo(midX - distance, midY + maxRadius)
          this.ctx.lineTo(midX - distance, midY - maxRadius)
          this.ctx.stroke()
          // Horizontal CH
          this.ctx.beginPath()
          this.ctx.moveTo(midX - maxRadius, midY + distance)
          this.ctx.lineTo(midX + maxRadius, midY + distance)
          this.ctx.stroke()
          this.ctx.beginPath()
          this.ctx.moveTo(midX - maxRadius, midY - distance)
          this.ctx.lineTo(midX + maxRadius, midY - distance)
          this.ctx.stroke()
        }
      }
    }

    // E-Beams
    const ebeamThickness = this._camera.getEBeamLineThickness()
    for(let i in drawableObjects.ebeamRays) {
      let ray = drawableObjects.ebeamRays[i]
      this.ctx.beginPath()
      this.ctx.strokeStyle = ray.color
      this.ctx.lineWidth = ebeamThickness
      this.ctx.moveTo(ray.startPoint.x, ray.startPoint.y)
      this.ctx.lineTo(ray.endPoint.x, ray.endPoint.y)
      this.ctx.stroke()
    }

    // lower right corner
    let lrcYOffset = this._camera.canvasHeight - 30
    let lrcYInterval = 40
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
    this.ctx.fillStyle = this._api.frameData.ship.alive ? '#ffffff' : "#ff0000";
    this.ctx.textAlign = 'left'
    this.ctx.fillText(scaleLabel, lrcXOffset + 8, lrcYOffset - 12)
    lrcYOffset -= lrcYInterval
    this.ctx.beginPath()
    this.ctx.font = '20px Courier New'
    this.ctx.fillText("Ensign " + this._user.handle, lrcXOffset, lrcYOffset)
    lrcYOffset -= lrcYInterval
    // Red alerts
    lrcYInterval = 30
    this.ctx.font = 'bold 22px courier new'
    const redalertColorAlpha = this._api.frameData.game_frame % 70 > 35 ? "1" : "0.65"
    this.ctx.fillStyle = `rgb(255, 2, 2, ${redalertColorAlpha})`
    if(this._api.frameData.ship.fuel_level < 1200) {
      this.ctx.beginPath()
      this.ctx.fillText("⚠️ LOW FUEL", lrcXOffset, lrcYOffset)
      lrcYOffset -= lrcYInterval
    }
    if(this._api.frameData.ship.battery_power < 45000) {
      this.ctx.beginPath()
      this.ctx.fillText("⚠️ LOW POWER", lrcXOffset, lrcYOffset)
      lrcYOffset -= lrcYInterval
    }

    // Front center and alerts
    if (this._api.frameData.winning_team == this._api.frameData.ship.team_id) {
      this.ctx.beginPath()
      this.ctx.font = 'bold 65px courier new'
      this.ctx.fillStyle = '#ffffff'
      this.ctx.textAlign = 'center'
      this.ctx.fillText("SUCCESS 🏆🚀", this._camera.canvasHalfWidth, this._camera.canvasHalfHeight / 2)
    }
    else if(!this._api.frameData.ship.alive) {
      this.ctx.beginPath()
      this.ctx.font = 'bold 56px courier new'
      this.ctx.fillStyle = '#ff0000'
      this.ctx.textAlign = 'center'
      let deathTextYOffset = this._camera.canvasHalfHeight / 3
      const deathQuoteOffset = 50
      if(this._api.frameData.game_frame % 50 > 25) {
        this.ctx.fillText("GAME OVER", this._camera.canvasHalfWidth, deathTextYOffset)
      }
      deathTextYOffset += (deathQuoteOffset * 2)
      this.ctx.beginPath()
      this.ctx.fillStyle = '#9e9e9e'
      this.ctx.textAlign = 'left'
      this.ctx.font = 'bold 40px Verdana'
      for(let i in this.deathQuote.lines) {
        const prefix = parseInt(i) === 0 ? '"' : ""
        this.ctx.fillText(prefix + this.deathQuote.lines[i], 100, deathTextYOffset)
        deathTextYOffset += deathQuoteOffset
      }
      this.ctx.font = 'bold 32px Verdana'
      deathTextYOffset += deathQuoteOffset * 0.5
      this.ctx.beginPath()
      this.ctx.fillText("- " + (this.deathQuote.author || "Unknown"), 100, deathTextYOffset)

    }
    // Resources (TOP LEFT)
    const tlcYInterval = 34
    const tlcKFYInterval = 28
    let tlcYOffset = 25
    const tlcXOffset = 15
    if(this._api.frameData.ship.alive){
      this.ctx.beginPath()
      this.ctx.font = '24px Courier New'
      this.ctx.fillStyle = '#fcb8b8'
      this.ctx.textAlign = 'left'
      this.ctx.fillText("⛽ " + this._formatting.formatNumber(this._api.frameData.ship.fuel_level), tlcXOffset, tlcYOffset)
      tlcYOffset += tlcYInterval

      this.ctx.beginPath()
      this.ctx.fillStyle = '#fcf9b8'
      this.ctx.fillText("🔋 " + this._formatting.formatNumber(this._api.frameData.ship.battery_power), tlcXOffset, tlcYOffset)
      tlcYOffset += tlcYInterval

      this.ctx.beginPath()
      this.ctx.fillStyle = '#ffffff'
      this.ctx.fillText("🎥 " + this._camera.getMode().toUpperCase(), tlcXOffset, tlcYOffset)
      tlcYOffset += tlcYInterval
    }
    // Killfeed (TOP LEFT)
    tlcYOffset += tlcYInterval
    this.ctx.font = '20px Courier New'
    this.ctx.fillStyle = '#ffffff'
    this.ctx.textAlign = 'left'
    for(let i in this._api.frameData.killfeed) {
      const kfe = this._api.frameData.killfeed[i]
      this.ctx.beginPath()
      this.ctx.fillText("💀 " + kfe.victim_name, tlcXOffset, tlcYOffset)
      tlcYOffset += tlcKFYInterval
    }

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
    if(this._api.frameData.ship.alive){
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
    }
    // Gyroscope
    if(!this.isDebug && this._api.frameData.ship.alive) {
      // Circle
      const buffer = 3;
      const gryroscopeRadius = Math.floor(this._camera.canvasHalfHeight / 8)
      const gryroscopeX = this._camera.canvasWidth - (gryroscopeRadius + buffer)
      const gryroscopeY = gryroscopeRadius + buffer
      this.ctx.beginPath()
      this.ctx.fillStyle = "rgb(255, 255, 255, 0.65)"
      this.ctx.arc(
        gryroscopeX,
        gryroscopeY,
        gryroscopeRadius,
        0,
        2 * Math.PI,
      )
      this.ctx.fill()
      // Velocity Line
      if(
        this._api.frameData.ship.velocity_x_meters_per_second
        || this._api.frameData.ship.velocity_y_meters_per_second
      ) {
        const angleRads = this._camera.getCanvasAngleBetween(
          {x:0, y:0},
          {
            x: gryroscopeX + this._api.frameData.ship.velocity_x_meters_per_second * 1000,
            y: gryroscopeY + this._api.frameData.ship.velocity_y_meters_per_second * 1000,
          }
        ) * (Math.PI / 180)
        const gyroLinePointB = {
          x: gryroscopeX + Math.round(gryroscopeRadius * Math.sin(angleRads)),
          y: gryroscopeY + Math.round(gryroscopeRadius * Math.cos(angleRads)),
        }
        this.ctx.beginPath()
        this.ctx.strokeStyle = '#000000'
        this.ctx.lineWidth = 4
        this.ctx.moveTo(gryroscopeX, gryroscopeY)
        this.ctx.lineTo(gyroLinePointB.x, gyroLinePointB.y)
        this.ctx.stroke()
      }
      // Scanner Traversal Crosshairs
      if(this._api.frameData.ship.scanner_lock_traversal_slack !== null) {
        const crossOffset = gryroscopeRadius * this._api.frameData.ship.scanner_lock_traversal_slack
        this.ctx.beginPath()
        this.ctx.strokeStyle = 'rgb(255, 0, 0, 0.75)'
        this.ctx.lineWidth = 4
        // Verticle hairs
        this.ctx.moveTo(gryroscopeX - crossOffset, gryroscopeY - gryroscopeRadius)
        this.ctx.lineTo(gryroscopeX - crossOffset, gryroscopeY + gryroscopeRadius)
        this.ctx.stroke()
        this.ctx.beginPath()
        this.ctx.moveTo(gryroscopeX + crossOffset, gryroscopeY - gryroscopeRadius)
        this.ctx.lineTo(gryroscopeX + crossOffset, gryroscopeY + gryroscopeRadius)
        this.ctx.stroke()

        // Horizontal hairs
        this.ctx.beginPath()
        this.ctx.moveTo(gryroscopeX - gryroscopeRadius, gryroscopeY - crossOffset)
        this.ctx.lineTo(gryroscopeX + gryroscopeRadius, gryroscopeY - crossOffset)
        this.ctx.stroke()
        this.ctx.beginPath()
        this.ctx.moveTo(gryroscopeX - gryroscopeRadius, gryroscopeY + crossOffset)
        this.ctx.lineTo(gryroscopeX + gryroscopeRadius, gryroscopeY + crossOffset)
        this.ctx.stroke()
      }
      // Velocity Text
      const velocity = Math.sqrt(
        Math.pow(this._api.frameData.ship.velocity_x_meters_per_second, 2)
        + Math.pow(this._api.frameData.ship.velocity_y_meters_per_second, 2)
      ).toFixed(1)
      this.ctx.beginPath()
      this.ctx.font = 'bold 22px Courier New'
      this.ctx.fillStyle = 'rgb(255, 181, 43,  0.95)'
      this.ctx.textAlign = 'right'
      this.ctx.fillText(
        velocity + " M/S",
        this._camera.canvasWidth - 3,
        gryroscopeY + gryroscopeRadius + 18,
      )
      // Thermal Signature Text
      this.ctx.fillText(
        this._api.frameData.ship.scanner_thermal_signature + " IR ",
        this._camera.canvasWidth - 3,
        gryroscopeY + gryroscopeRadius + 40,
      )
    }

    // Click feedback
    if(this.clickAnimationFrame) {
      this.ctx.beginPath()
      this.ctx.strokeStyle = "#00ff00"
      this.ctx.lineWidth = 3
      this.ctx.arc(
        this.clickAnimationCanvasX,
        this.clickAnimationCanvasY,
        this.clickAnimationFrame * 2.5,
        0,
        2 * Math.PI,
      )
      this.ctx.stroke()
      this.clickAnimationFrame++
      if (this.clickAnimationFrame > 10) {
        this.clickAnimationFrame = null
      }
    }

    if(this._api.frameData.ship.scanner_data.length && !this.scannerTargetIDCursor) {
      this.scannerTargetIDCursor = this._api.frameData.ship.scanner_data[0].id
    }

    window.requestAnimationFrame(this.paintDisplay.bind(this))

  }

  private clearCanvas(): void {
    this.ctx.beginPath()
    this.ctx.clearRect(0, 0, this._camera.canvasWidth * 2, this._camera.canvasHeight * 2) // *2 because of bug where corner is not cleared
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


  private async setCameraToPilotMode() {
    if(this._camera.getMode() == CAMERA_MODE_FREE) {
      this._camera.setModeShip()
      this._camera.setZoomIndex(3)
    }
  }

  public async btnActivateEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'activate_engine'},
    )
    setTimeout(()=>{this.setCameraToPilotMode()})
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
    setTimeout(()=>{this.setCameraToPilotMode()})
  }

  public async btnBoostEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'boost_engine'},
    )
  }

  public async btnUnlightEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'unlight_engine'},
    )
  }

  public async btnActivateAPU() {
    await this._api.post(
      "/api/rooms/command",
      {command:'activate_apu'},
    )
  }

  public async btnDeactivateAPU() {
    await this._api.post(
      "/api/rooms/command",
      {command:'deactivate_apu'},
    )
  }

  public async btnSetScannerModeRadar() {
    await this._api.post(
      "/api/rooms/command",
      {command:'set_scanner_mode_radar'},
    )
  }

  public async btnSetScannerModeIR() {
    await this._api.post(
      "/api/rooms/command",
      {command:'set_scanner_mode_ir'},
    )
  }

  public async btnActivateScanner() {
    await this._api.post(
      "/api/rooms/command",
      {command:'activate_scanner'},
    )
    setTimeout(()=>{this._camera.setModeScanner()})
  }

  public async btnDeactivateScanner() {
    this.scannerTargetIDCursor = null
    await this._api.post(
      "/api/rooms/command",
      {command:'deactivate_scanner'},
    )
  }

  // Autopilot button handlers.
  public async btnDisableAutoPilot() {
    await this._api.post(
      "/api/rooms/command",
      {command:'disable_autopilot'},
    )
  }
  public async btnAutoPilotHaltPosition() {
    await this._api.post(
      "/api/rooms/command",
      {command:'run_autopilot', autopilot_program:'position_hold'},
    )
  }
  public async btnAutoPilotHeadingLockTarget() {
    await this._api.post(
      "/api/rooms/command",
      {command:'run_autopilot', autopilot_program:'lock_target'},
    )
  }
  public async btnAutoPilotHeadingLockPrograde() {
    await this._api.post(
      "/api/rooms/command",
      {command:'run_autopilot', autopilot_program:'lock_prograde'},
    )
  }
  public async btnAutoPilotHeadingLockRetrograde() {
    await this._api.post(
      "/api/rooms/command",
      {command:'run_autopilot', autopilot_program:'lock_retrograde'},
    )
  }

  btnClickScannerCursorUp() {
    if(!this._api.frameData.ship || !this._api.frameData.ship.scanner_online) {
      this.scannerTargetIDCursor = null
      return
    }
    if(!this._api.frameData.ship.scanner_data.length) {
      this.scannerTargetIDCursor = null
      return
    }
    if(this.scannerTargetIDCursor === null) {
      this.scannerTargetIDCursor = this._api.frameData.ship.scanner_data[this._api.frameData.ship.scanner_data.length - 1].id
    }
    else {
      const currentIndex = this._api.frameData.ship.scanner_data.map(sc => sc.id).indexOf(this.scannerTargetIDCursor)
      if(currentIndex === -1) {
        this.scannerTargetIDCursor = this._api.frameData.ship.scanner_data[this._api.frameData.ship.scanner_data.length - 1].id
      }
      else {
        const targetIndex = currentIndex === 0 ? this._api.frameData.ship.scanner_data.length - 1 : currentIndex - 1
        this.scannerTargetIDCursor = this._api.frameData.ship.scanner_data[targetIndex].id
      }
    }
  }

  btnClickScannerCursorDown() {
    if(!this._api.frameData.ship || !this._api.frameData.ship.scanner_online) {
      this.scannerTargetIDCursor = null
      return
    }
    if(!this._api.frameData.ship.scanner_data.length) {
      this.scannerTargetIDCursor = null
      return
    }
    if(this.scannerTargetIDCursor === null) {
      this.scannerTargetIDCursor = this._api.frameData.ship.scanner_data[0].id
    }
    else {
      const currentIndex = this._api.frameData.ship.scanner_data.map(sc => sc.id).indexOf(this.scannerTargetIDCursor)
      if(currentIndex === -1) {
        this.scannerTargetIDCursor = this._api.frameData.ship.scanner_data[0].id
      }
      else {
        const targetIndex = currentIndex === this._api.frameData.ship.scanner_data.length - 1 ? 0 : currentIndex + 1
        this.scannerTargetIDCursor = this._api.frameData.ship.scanner_data[targetIndex].id
      }
    }
  }

  async btnClickScannerCursorLock () {
    if(!this._api.frameData.ship || !this._api.frameData.ship.scanner_online) {
      this.scannerTargetIDCursor = null
      return
    }
    const targetIndex = this._api.frameData.ship.scanner_data.map(sc => sc.id).indexOf(this.scannerTargetIDCursor)
    if(targetIndex === -1) {
      this.scannerTargetIDCursor = null
      return
    }
    if(this.scannerTargetIDCursor === null) {
      return
    }
    if(this._api.frameData.ship.scanner_locking) {
      return
    }
    if(this._api.frameData.ship.scanner_locked && this.scannerTargetIDCursor === this._api.frameData.ship.scanner_lock_target) {
      return
    }
    await this._api.post(
      "/api/rooms/command",
      {command: 'set_scanner_lock_target', target: this.scannerTargetIDCursor},
    )
  }

  async btnClickChargeEBeam() {
    if(!this._api.frameData.ship.ebeam_charging && !this._api.frameData.ship.ebeam_firing) {
      await this._api.post(
        "/api/rooms/command",
        {command:'charge_ebeam'},
      )
    }
  }

  async btnClickPauseChargeEBeam() {
    if(this._api.frameData.ship.ebeam_charging) {
      await this._api.post(
        "/api/rooms/command",
        {command:'pause_charge_ebeam'},
      )
    }
  }

  async btnClickFireEBeam() {
    if(this._api.frameData.ship.ebeam_can_fire) {
      await this._api.post(
        "/api/rooms/command",
        {command:'fire_ebeam'},
      )
    }
  }

  async btnToggleAllChatPane(){
    this._pane.toggleAllChatPane()
  }

  btnToggleMainMenuPane() {
    this._pane.toggleMainMenuPane()
  }

  async btnToggleShipPane(){
    this._pane.toggleShipPane()
  }

}
