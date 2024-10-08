import { Component, OnInit, ElementRef, ViewChild } from '@angular/core';
import { Subscription } from 'rxjs'
import { ApiService } from '../api.service';

import { CameraService } from '../camera.service';
import { PaneService } from '../pane.service';
import { ScannerService } from '../scanner.service';
import { DrawingService } from '../drawing.service';
import {
  TIMER_SLUG_SCANNER_STARTUP,
  TIMER_SLUG_SCANNER_LOCKING,
} from "../constants"
import { TimerItem } from "../models/timer-item.model"
import { ScannerDataShipElement } from '../models/apidata.model';
import { DrawableCanvasItems } from '../models/drawable-objects.model'

const randomInt = function (min: number, max: number): number  {
  return Math.floor(Math.random() * (max - min) + min)
}

const randomFloat = function (min: number, max: number): number  {
  return Math.random() * (max - min) + min
}

@Component({
  selector: 'app-scannerpane',
  templateUrl: './scannerpane.component.html',
  styleUrls: ['./scannerpane.component.css']
})
export class ScannerpaneComponent implements OnInit {


  @ViewChild("paneElement") paneElement: ElementRef
  @ViewChild("graphicsCanvas") canvas: ElementRef
  @ViewChild("titleBar") titleBar: ElementRef
  zIndexesUpdatedSubscription: Subscription

  private ctx: CanvasRenderingContext2D | null = null

  private bgColorRadar = "#001800"   // dark green
  private bgColorIR = "#0f0018"      // dark purple
  private bgColorOffline = "#181818" // dark gray
  private maxCameraZoom: number
  private minCameraZoom: number

  private maxLockingModLength = 30
  private lockingCounter = 0
  private minOnCount = 10
  private onForCount = 0

  constructor(
    public _pane: PaneService,
    private _camera: CameraService,
    private _api: ApiService,
    private _scanner: ScannerService,
    private _draw: DrawingService,
  ) {
  }

  ngOnInit(): void {
    this.maxCameraZoom = this._camera.scannerPaneCamera.getMaxZoom()
    this.minCameraZoom = this._camera.scannerPaneCamera.getMinZoom()

    this.zIndexesUpdatedSubscription = this._pane.zIndexesUpdated.subscribe((zIndexes: string[]) => {
      const paneZIndex = zIndexes.indexOf(this._pane.PANE_SCANNER);
      if(paneZIndex === -1) {
        return console.error(
          "cannot find paneName " + this._pane.PANE_SCANNER + " in zIndexes " + JSON.stringify(zIndexes))
      }
      this.paneElement.nativeElement.style.zIndex = paneZIndex
      const isSelected = paneZIndex == (zIndexes.length - 1) // Pane is "top" if it's in the last zindex postion.
      if(isSelected) {
        this.paneElement.nativeElement.style.border = "1px solid #33002d"
      } else {
        this.paneElement.nativeElement.style.removeProperty("border")
      }
    })
  }
  ngOnDestroy() {
    this.zIndexesUpdatedSubscription.unsubscribe()
  }
  ngAfterViewInit() {
    this.paneElement.nativeElement.addEventListener('mouseenter', ()=>{
      this._pane.registerMouseEnteringPane(this._pane.PANE_SCANNER)
    })
    this.paneElement.nativeElement.addEventListener('mouseleave', ()=>{
      this._pane.registerMouseLeavingPane(this._pane.PANE_SCANNER)
    })
    this.setupCanvasContext()
    this.select()
    this.resizeCanvas()
    this.canvas.nativeElement.style.backgroundColor = "#001800"
    setTimeout(()=>{
      this.paintDisplay()
    })
  }

  private setupCanvasContext(): void {
    this.ctx = this.ctx || this.canvas.nativeElement.getContext("2d")
  }

  select() {
    this._pane.addToTopOfZIndexes(this._pane.PANE_SCANNER)
  }

  paneResized($event: any) {
    this.resizeCanvas()
  }

  private resizeCanvas() {
    setTimeout(() => {
      console.log("resizeCanvas()")
      const height = this.paneElement.nativeElement.offsetHeight - this.titleBar.nativeElement.offsetHeight
      this.canvas.nativeElement.width = this.canvas.nativeElement.offsetWidth
      this.canvas.nativeElement.height = height// this.canvas.nativeElement.offsetHeight
      this._camera.scannerPaneCamera.registerCanvasWidthHeight(
        this.canvas.nativeElement.offsetWidth,
        this.canvas.nativeElement.offsetHeight,
      )
    })
  }

  private anyTargetsOnScope(): boolean {
    return this._api.frameData.ship.scanner_ship_data.length > 0
  }

  private setCanvasBGColor(): void {
    this.ctx.beginPath()
    if (this._api.frameData.ship.scanner_starting) {
      const v = randomInt(10, 25)
      this.ctx.fillStyle = `rgb(${v}, ${v}, ${v})`
    } else if(!this._api.frameData.ship.scanner_starting && !this._api.frameData.ship.scanner_online) {
      this.ctx.fillStyle = this.bgColorOffline
    } else if(this._api.frameData.ship.scanner_online && this._api.frameData.ship.scanner_mode == "radar") {
      this.ctx.fillStyle = this.bgColorRadar
    } else if(this._api.frameData.ship.scanner_online && this._api.frameData.ship.scanner_mode == "ir") {
      this.ctx.fillStyle = this.bgColorIR
    } else {throw new Error("unknown mode")}
    this.ctx.rect(
      0, 0,
      this._camera.scannerPaneCamera.canvasWidth * 2,  // *2 because of bug where corner is not cleared
      this._camera.scannerPaneCamera.canvasHeight * 2, //
    )
    this.ctx.fill()
  }

  private clearCanvas(): void {
    this.ctx.beginPath()
    this.ctx.clearRect(
      0, 0,
      this._camera.scannerPaneCamera.canvasWidth * 2,  // *2 because of bug where corner is not cleared
      this._camera.scannerPaneCamera.canvasHeight * 2, //
    )
  }

  private paintDisplay(): void {
    const ship = this._api.frameData.ship
    this.clearCanvas()
    this.setCanvasBGColor()

    if(!ship.scanner_online) {
      this.drawScannerUnavailableMessage()
      window.requestAnimationFrame(this.paintDisplay.bind(this))
      return
    }

    const anyTargets = this.anyTargetsOnScope()

    // Select a target if any are available and not are selected.
    if(anyTargets && !this._scanner.scannerTargetIDCursor) {
      this._scanner.scannerTargetIDCursor = this._api.frameData.ship.scanner_ship_data[0].id
      this._scanner.scannertTargetIndex = 0
    }

    let target: ScannerDataShipElement

    // Draw scene of selected target
    let drawableObjects: DrawableCanvasItems
    const overlayAlpha = randomFloat(0.62, 0.95)
    if(anyTargets) {
      target = this._api.frameData.ship.scanner_ship_data[this._scanner.scannertTargetIndex]
      if(!target) {
        this._scanner.scannerTargetIDCursor = null
        this._scanner.scannertTargetIndex = null
        window.requestAnimationFrame(this.paintDisplay.bind(this))
        return
      }
      drawableObjects = this._camera.scannerPaneCamera.getDrawableCanvasObjects()
      this._camera.scannerPaneCamera.setPosition(
        target.coord_x, target.coord_y,
      )
      this.drawGameScene(drawableObjects)
      this.drawBottomLeftOverlay(overlayAlpha)
    }
    this.drawTopLeftOverlay(overlayAlpha)
    this.drawBottomCenterAlert(overlayAlpha)
    this.drawTopRightOverlay(overlayAlpha)

    if(anyTargets && (this._api.frameData.ship.scanner_locking || this._api.frameData.ship.scanner_locked)) {
      this.drawLockVisualIndicator(overlayAlpha, drawableObjects)
    }

    window.requestAnimationFrame(this.paintDisplay.bind(this))
  }

  private drawGameScene(drawableObjects: DrawableCanvasItems) {

    // Add map features
    this._draw.drawSpaceStations(this.ctx, this._camera.scannerPaneCamera)
    this._draw.drawMiningLocations(this.ctx, this._camera.scannerPaneCamera)

    // Flame smoke elements
    this._draw.drawVisualFlameSmokeElements(
      this.ctx, this._camera.scannerPaneCamera,
      this._camera.getFlameSmokeElements()
    )
    // Visual Velocity elements
    this._draw.drawVisualVelocityElements(
      this.ctx, this._camera.scannerPaneCamera,
      this._camera.getVelocityTrailElements(),
    )
    this._draw.drawEMPTrailElements(
      this.ctx, this._camera.scannerPaneCamera,
      this._camera.getEMPTrailElements(),
    )

    if(drawableObjects.shipVisionCircle) {
      this._draw.drawVelocityAndHeadingLine(
        this.ctx,
        this._camera.scannerPaneCamera,
        drawableObjects.shipVisionCircle,
        true,
      )
    }
    this._draw.drawLineToScannerCursor(
      this.ctx,
      this._camera.scannerPaneCamera,
      this._scanner.scannerTargetIDCursor,
    )

    // Ships
    const drawBoundingBox = false
    for(let i in drawableObjects.ships) {
      this._draw.drawShip(
        this.ctx,
        this._camera.scannerPaneCamera,
        drawableObjects.ships[i],
        this._scanner.scannerTargetIDCursor,
        drawBoundingBox,
      )
    }
    // magnet mines
    for(let i in drawableObjects.magnetMines) {
      this._draw.drawMagnetMine(this.ctx, drawableObjects.magnetMines[i])
    }
    this._draw.drawMagnetMineTargetingLines(
      this.ctx,
      drawableObjects.magnetMineTargetingLines
    )
    // Hunter Drones
    for(let i in drawableObjects.hunterDrones) {
      this._draw.drawHunterDrone(
        this.ctx,
        this._camera.scannerPaneCamera,
        drawableObjects.hunterDrones[i],
      )
    }
    // EMPs
    for(let i in drawableObjects.emps) {
      this._draw.drawEMP(this.ctx, drawableObjects.emps[i])
    }

    this._draw.drawShipGravityBrakeEffectElements(
      this.ctx,
      this._camera.scannerPaneCamera,
      this._camera.getGravityBrakeShipEffectElements(),
    )

    // Explosion FX
    this._draw.drawExplosionShockwaves(this.ctx, this._camera.scannerPaneCamera)
    this._draw.drawExplosions(this.ctx, this._camera.scannerPaneCamera)

    // EMP blasts
    this._draw.drawEMPBlasts(this.ctx, this._camera.scannerPaneCamera)

    // E-Beams
    this._draw.drawEbeams(this.ctx, this._camera.scannerPaneCamera, drawableObjects.ebeamRays)
    this._draw.drawEBeamFiringEffectElements(
      this.ctx,
      this._camera.scannerPaneCamera,
      this._camera.getEBeamFiringEffectElements(),
    )
  }

  private drawScannerUnavailableMessage() {
    const isStarting = this._api.frameData.ship.scanner_starting
    this.ctx.beginPath()
    this.ctx.font = 'bold 40px Courier New'
    this.ctx.fillStyle = '#ffffff'
    this.ctx.textAlign = 'center'
    this.ctx.textBaseline = "bottom"
    this.ctx.fillText(
      isStarting ? "LOADING" : "NO DATA",
      this._camera.scannerPaneCamera.canvasHalfWidth,
      this._camera.scannerPaneCamera.canvasHeight / 3,
    )
    if(isStarting){
      this.drawLoadingBar()
    }
  }
  private drawLoadingBar() {
    const timer: TimerItem | undefined = this._api.frameData.ship.timers.find(
      t => t.slug === TIMER_SLUG_SCANNER_STARTUP)
    if(!timer) {
      return
    }
    const barOutlineX1 = Math.floor(this._camera.scannerPaneCamera.canvasWidth * 0.125)
    const barOutlineX2 = Math.floor(this._camera.scannerPaneCamera.canvasWidth * 0.875)
    const xLen = barOutlineX2 - barOutlineX1
    const barOutlineY1 = this._camera.scannerPaneCamera.canvasHalfHeight
    const barOutlineY2 = this._camera.scannerPaneCamera.canvasHalfHeight + 25
    const barFillLen = Math.floor(xLen * (timer.percent / 100))
    this.ctx.beginPath() // Loading Bar Outline
    this.ctx.strokeStyle = "#ffffff"
    this.ctx.lineWidth = 1
    this.ctx.rect(
      barOutlineX1, barOutlineY1,
      xLen,
      barOutlineY2 - barOutlineY1
    )
    this.ctx.stroke()
    this.ctx.beginPath() // Loading Bar Fill
    this.ctx.fillStyle = "#ffffff"
    this.ctx.rect(
      barOutlineX1, barOutlineY1,
      barFillLen,
      barOutlineY2 - barOutlineY1
    )
    this.ctx.fill()

  }

  private drawTopRightOverlay(alpha:  number) {
    // Target Stats
    const anyTargets = this.anyTargetsOnScope()
    let yOffset = 5
    const xOffset = this._camera.scannerPaneCamera.canvasWidth - 5
    const yInterval = 22
    this.ctx.beginPath()
    this.ctx.font = 'bold 23px Courier New'
    this.ctx.fillStyle = `rgb(255, 255, 255, ${alpha})`
    this.ctx.textAlign = 'right'
    this.ctx.textBaseline = "top"
    let txt = (
      anyTargets
      ? `TARGET ${this._scanner.scannertTargetIndex + 1}/${this._api.frameData.ship.scanner_ship_data.length}`
      : "NO TARGET"
    )
    this.ctx.fillText(txt, xOffset, yOffset)
    if(!anyTargets) {
      return
    }
    yOffset += (yInterval + 3)

    this.ctx.beginPath()
    this.ctx.font = 'italic 20px Courier New'
    let target: ScannerDataShipElement
    if(anyTargets) {
      target = this._api.frameData.ship.scanner_ship_data[this._scanner.scannertTargetIndex]
      this.ctx.fillText(
        target.designator.toUpperCase(), xOffset, yOffset
      )
      yOffset += yInterval
    } else {
      return
    }

    this.ctx.font = '20px Courier New'
    this.ctx.beginPath()
    this.ctx.fillText(
      `DIST. ${target.distance} M`, xOffset, yOffset
    )
    yOffset += yInterval

    this.ctx.beginPath()
    this.ctx.fillText(
      `BEARING ${target.relative_heading}°`, xOffset, yOffset
    )
    yOffset += yInterval

    this.ctx.beginPath()
    const mode = this._api.frameData.ship.scanner_mode
    if(mode == "radar") {
      const antiRadar = target.anti_radar_coating_level
      this.ctx.fillText(
        `ANTI RADAR ${antiRadar}`, xOffset, yOffset
      )
    } else if (mode == "ir") {
       target.scanner_thermal_signature
       this.ctx.fillText(
        `SIGNATURE ${target.scanner_thermal_signature}`, xOffset, yOffset
      )
    } else { throw new Error(`unknown scanner mode ${this._api.frameData.ship.scanner_mode}`)}
    yOffset += yInterval
  }

  private drawTopLeftOverlay(alpha: number) {
    // Scanner Stats
    let yOffset = 5;
    const xOffset = 5
    const yTextInterval = 20
    this.ctx.beginPath()
    this.ctx.font = 'bold 23px Courier New'
    this.ctx.fillStyle = `rgb(255, 255, 255, ${alpha})`
    this.ctx.textAlign = 'left'
    this.ctx.textBaseline = "top"
    this.ctx.fillText(
      "SCAN STATS", xOffset, yOffset
    )
    yOffset += (yTextInterval + 3)

    let mode: string;
    if(this._api.frameData.ship.scanner_mode == "radar") {
      mode = "RADAR"
    } else if(this._api.frameData.ship.scanner_mode == "ir") {
      mode = "THERMAL"
    } else { throw new Error(`unknown scanner mode ${this._api.frameData.ship.scanner_mode}`)}

    this.ctx.beginPath()
    this.ctx.font = '20px Courier New'
    this.ctx.fillStyle = `rgb(255, 255, 255, ${alpha})`
    this.ctx.textAlign = 'left'
    this.ctx.textBaseline = "top"
    this.ctx.fillText(
      "MODE " + mode, xOffset, yOffset
    )
    yOffset += yTextInterval

    this.ctx.beginPath()
    let text: string
    if(mode == "RADAR") {
      text = "RANGE " + this._api.frameData.ship.scanner_radar_range
    } else if (mode == "THERMAL") {
      text = "RANGE " + this._api.frameData.ship.scanner_ir_range
    } else { throw new Error(`unknown scanner mode ${mode}`)}
    this.ctx.fillText(
      text, xOffset, yOffset
    )
    yOffset += yTextInterval

    this.ctx.beginPath()
    text;
    if(mode == "RADAR") {
      text = "SENS " + this._api.frameData.ship.scanner_radar_sensitivity
    } else if (mode == "THERMAL") {
      text = "MIN " + this._api.frameData.ship.scanner_ir_minimum_thermal_signature
    } else { throw new Error(`unknown scanner mode ${mode}`)}
    this.ctx.fillText(
      text, xOffset, yOffset
    )
    yOffset += yTextInterval

    this.ctx.beginPath()
    if(!this._api.frameData.ship.scanner_locked) {
      text = `MAX Δ° ${this._api.frameData.ship.scanner_locking_max_traversal_degrees}`
    } else {
      text = `MAX Δ° ${this._api.frameData.ship.scanner_locked_max_traversal_degrees}`
    }
    this.ctx.fillText(
      text, xOffset, yOffset
    )
    yOffset += yTextInterval
  }

  private drawBottomCenterAlert(alpha) {
    let text: string
    const useYellow = this._api.frameData.ship.scanner_mode == "ir"
    if(this._api.frameData.ship.scanner_locking) {
      text = "LOCKING"
    } else if(this._api.frameData.ship.scanner_locked) {
      text = "~LOCKED~"
    } else {
      text = "SEARCH"
    }
    this.ctx.beginPath()
    this.ctx.textAlign = 'center'
    this.ctx.textBaseline = "bottom"
    this.ctx.font = 'bold 23px Courier New'
    this.ctx.fillStyle = this._api.frameData.ship.scanner_locked ? `rgb(255, ${useYellow?'255':'0'}, 0, ${alpha*1.3})`:`rgb(255, 255, 255, ${alpha})`
    // FIXME: adding extra pixels because canvas extends a few px beyond the pane
    const yOffset = this._camera.scannerPaneCamera.canvasHeight - (6 + 5)
    this.ctx.fillText(
      text, this._camera.scannerPaneCamera.canvasHalfWidth, yOffset
    )
  }

  private drawBottomLeftOverlay(alpha: number) {
    // Zoom Info
    const color = `rgb(255, 255, 255, ${alpha})`
    this.ctx.font = '20px Courier New'
    this.ctx.fillStyle = color
    this.ctx.textAlign = 'left'
    this.ctx.textBaseline = "bottom"
    let yOffset = this._camera.scannerPaneCamera.canvasHeight - 15
    const xOffset = 8

    this.ctx.beginPath()
    this.ctx.fillText(
      `ZOOM ${this._camera.scannerPaneCamera.getZoom()}`, xOffset, yOffset
    )
    yOffset -= 25

    // Zoom bar
    const barHeight = 15
    const barWidth = 100
    const y1 = yOffset - barHeight
    this.ctx.beginPath()
    this.ctx.strokeStyle = color
    this.ctx.lineWidth = 2
    this.ctx.rect(
      xOffset, y1, barWidth, barHeight
    )
    this.ctx.stroke()

    // Zoom Bar Indicator line
    const percent = (this._camera.scannerPaneCamera.getZoom() - this.minCameraZoom) / (this.maxCameraZoom - this.minCameraZoom)
    const indicatorXOffset = xOffset + (barWidth * percent)
    const overdrawLip = 3
    const yTop = y1 - overdrawLip
    const yBottom = y1 + barHeight + overdrawLip
    this.ctx.beginPath()
    this.ctx.lineWidth = 4
    this.ctx.moveTo(indicatorXOffset, yTop)
    this.ctx.lineTo(indicatorXOffset, yBottom)
    this.ctx.stroke()
  }

  private drawLockVisualIndicator(alpha: number, drawableObjects: DrawableCanvasItems) {
    let lineWidth = 3
    const useYellow = this._api.frameData.ship.scanner_mode == "ir"
    if(this._api.frameData.ship.scanner_locking) {
      // If locking: blink crosshair, slow at first, faster as lock is obtained
      const timer = this._api.frameData.ship.timers.find(t => t.slug === TIMER_SLUG_SCANNER_LOCKING)
      if(!timer) {
        return console.warn("expected to find timer")
      }
      let skipCheck = false
      if(this.onForCount && this.onForCount < this.minOnCount) {
        this.onForCount++
        skipCheck = true
      } else if(this.onForCount && this.onForCount >= this.minOnCount) {
        this.onForCount = 0
        this.lockingCounter = 0
      }
      if(!skipCheck) {
        this.lockingCounter++
        const percent = timer.percent / 100
        const modDenominator = Math.max(1, Math.floor(this.maxLockingModLength * (1 - percent)))
        const mod = this.lockingCounter % modDenominator
        if (mod){
          return
        }
        this.onForCount = 1
      }
    } else {
      // If locked, no blinking, and
      lineWidth = 5
    }

    const target = drawableObjects.ships.find(s=> this._api.frameData.ship.scanner_lock_target == s.shipId)
    if(!target) {
      return console.warn("expected to find drawable ship")
    }
    const midX  = (target.canvasBoundingBox.x2 + target.canvasBoundingBox.x1) / 2
    const midY  = (target.canvasBoundingBox.y2 + target.canvasBoundingBox.y1) / 2
    const dx = target.canvasBoundingBox.x2 - target.canvasBoundingBox.x1
    const dy = target.canvasBoundingBox.y2 - target.canvasBoundingBox.y1
    const maxRadius = Math.max(dx, dy)
    const distance = maxRadius * this._api.frameData.ship.scanner_lock_traversal_slack
    // Vertical CrossHairs
    this.ctx.beginPath()
    this.ctx.strokeStyle = `rgb(255, ${useYellow?'255':'0'}, 0, ${alpha / 2})`
    this.ctx.lineWidth = lineWidth
    this.ctx.beginPath()
    this.ctx.moveTo(midX + distance, midY + maxRadius)
    this.ctx.lineTo(midX + distance, midY - maxRadius)
    this.ctx.stroke()
    this.ctx.beginPath()
    this.ctx.moveTo(midX - distance, midY + maxRadius)
    this.ctx.lineTo(midX - distance, midY - maxRadius)
    this.ctx.stroke()
    // Horizontal Crosshairs
    this.ctx.beginPath()
    this.ctx.moveTo(midX - maxRadius, midY + distance)
    this.ctx.lineTo(midX + maxRadius, midY + distance)
    this.ctx.stroke()
    this.ctx.beginPath()
    this.ctx.moveTo(midX - maxRadius, midY - distance)
    this.ctx.lineTo(midX + maxRadius, midY - distance)
    this.ctx.stroke()

    if(this._api.frameData.ship.scanner_locked && Math.random() < 0.8) {
      // Diamond Lock
      const buffer = 0//randomInt(-2, 2)
      this.ctx.beginPath()
      this.ctx.lineWidth = 2
      this.ctx.strokeStyle = `rgb(255, ${useYellow?'255':'0'}, 0, ${alpha / 2})`
      this.ctx.moveTo(midX, midY - (maxRadius + buffer)) // top mid
      this.ctx.lineTo(midX + maxRadius + buffer, midY) // mid right
      this.ctx.lineTo(midX, midY + maxRadius + buffer) // bottom mid
      this.ctx.lineTo(midX - (maxRadius + buffer), midY) // mid left
      this.ctx.lineTo(midX, midY - (maxRadius + buffer)) // top mid
      this.ctx.stroke()
    }
  }

}
