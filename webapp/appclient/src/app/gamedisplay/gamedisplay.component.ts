
import {
  Component,
  OnInit,
  ViewChild,
  ElementRef,
  HostListener,
} from '@angular/core'

import {
  DrawableCanvasItems,
} from '../models/drawable-objects.model'
import { BoxCoords } from '../models/box-coords.model'
import { ApiService } from "../api.service"
import { PaneService } from '../pane.service'
import { CameraService } from '../camera.service'
import { FormattingService } from '../formatting.service'
import { AllchatService } from "../allchat.service"
import { PointCoord } from '../models/point-coord.model'
import { DrawingService } from '../drawing.service'
import { SoundService } from '../sound.service'
import { ScannerService } from '../scanner.service'
import {
  TWO_PI,
  FEATURE_ORE,
  FEATURE_STATION,
  MAGNET_MINE_SLUG,
  EMP_SLUG,
} from '../constants'

const randomInt = function (min: number, max: number): number  {
  return Math.floor(Math.random() * (max - min) + min)
}

const CAMERA_MODE_SHIP = "ship"
const CAMERA_MODE_SCANNER = "scanner"
const CAMERA_MODE_MAP = "map"


enum ButtonGroup {
  NONE,
  ENGINE,
  AUTOPILOT,
  SCANNER,
  EMEBEAM,
  TORPEDO,
  UTILITIES,
}

class ButtonSizing {
  cornerOffset: number
  fontSize: number
  xLenMenu: number
  xLenEngineMenu: number
  xLenScannerC1Menu: number
  xLenScannerC2Menu: number
  xLenAutopilotMenu: number
  xLenEMEBeamMenu: number
  xLenTorpedoC1Menu: number
  xLenTorpedoC2Menu: number
  xLenUtilitiesMenu: number
  yLen: number
  xGap: number
  yGap: number
}

function getRandomFloat(min: number, max: number): number {
  return Math.random() * (max - min) + min;
}
@Component({
  selector: 'app-gamedisplay',
  templateUrl: './gamedisplay.component.html',
  styleUrls: ['./gamedisplay.component.css']
})
export class GamedisplayComponent implements OnInit {


  private activeBtnGroup = ButtonGroup.UTILITIES
  private btnCanvasLocations: {
    engineMenu?: BoxCoords,
    engineStartup?: BoxCoords,
    engineShutdown?: BoxCoords,
    engineIdle?: BoxCoords,
    engineIgnite?: BoxCoords,
    engineBoost?: BoxCoords,

    autoPilotMenu?: BoxCoords,
    autoPilotRetrograde?: BoxCoords,
    autoPilotPrograde?: BoxCoords,
    autoPilotWaypoint?: BoxCoords,
    autoPilotTarget?: BoxCoords,
    autoPilotHalt?: BoxCoords,
    autoPilotDisabled?: BoxCoords,

    scannerMenuBtn?: BoxCoords,
    scannerStartBtn?: BoxCoords,
    scannerStopBtn?: BoxCoords,
    scannerRadarBtn?: BoxCoords,
    scannerIRBtn?: BoxCoords,
    scannerUpArrowBtn?: BoxCoords,
    scannerDownArrowBtn?: BoxCoords,
    scannerLockBtn?: BoxCoords,

    EMEBeamMenuBtn?: BoxCoords,
    EMEBeamChargeBtn?: BoxCoords,
    EMEBeamPauseBtn?: BoxCoords,
    EMEBeamFireBtn?: BoxCoords,

    torpedoMenuBtn?: BoxCoords,
    torpedoMenuSelEMPBtn?: BoxCoords,
    torpedoMenuSelMagnetMineBtn?: BoxCoords,
    torpedoUpArrowBtn?: BoxCoords,
    torpedoDownArrowBtn?: BoxCoords,
    torpedoFireBtn?: BoxCoords,

    utilitiesMenuBtn?: BoxCoords,
    auxiliaryPowerBtn?: BoxCoords,
    oreMineBtn?: BoxCoords,
    gravityBrakeBtn?: BoxCoords,
  } = {}


  @ViewChild("graphicsCanvas") canvas: ElementRef

  private lauchVelocity: number = 60;
  private minLaunchVelocity = 10
  private maxLaunchVelocity = 120
  private launchVelocityInterval = 10

  private ctx: CanvasRenderingContext2D | null = null

  private cameraMode = CAMERA_MODE_SHIP
  private previousCameraMode: string | null = null
  private previousCameraZoomIndex = 4

  /* Props to track the user's mouse */
  private mouseInCanvas = true
  private mouseClickDownInCanvas = false
  private mousePanLastX: number | null = null
  private mousePanLastY: number | null = null
  private mouseMovedWhileDown = false

  /* Props to track click to change heading feedback */
  private clickHeadingAdjAnimationFrame: number | null = null
  private clickHeadingAdjAnimationCanvasX: number | null = null
  private clickHeadingAdjAnimationCanvasY: number | null = null

  /* Props to track button click feedback */
  private clickBtnClickAnimationFrame: number | null = null
  private clickBtnClickAnimationCanvasX: number | null = null
  private clickBtnClickAnimationCanvasY: number | null = null
  private clickBtnBoarderAnimationButtonName: string | null = null
  private clickBtnBoarderAnimationFrame: number | null = null


  /* Props used to hold debug data */
  private isDebug: boolean = false
  private lastFrameTime:any = null
  private clientFPS: number = 0
  private clientFrames: number = 0

  private drawableObjects: DrawableCanvasItems | null = null

  public gravBrakeBtnBkColor = "#000000"
  public grabBrakeBtnTxtColor = "#ff0000"
  public apuBtnBkColor = "#000000"
  public apuBtnTxtColor = "#ff0000"
  public mineBtnBkColor = "#ff0000"

  public wayPoint: PointCoord | null = null
  public wayPointUUID: string | null = null

  public selectedPneumaticWeapon = MAGNET_MINE_SLUG

  constructor(
    public _api: ApiService,
    public _camera: CameraService,
    public _pane: PaneService,
    public _allchat: AllchatService,
    public _scanner: ScannerService,
    private _sound: SoundService,
    private _draw: DrawingService,
    private _formatting: FormattingService,
  ) {
    console.log("GamedisplayComponent::constructor")
  }

  ngOnInit(): void {
    console.log("GamedisplayComponent::ngOnInit")

    this._scanner.scannerTargetIDCursor = null

    setTimeout(()=>{
      this.registerMouseEventListener()
      this.paintDisplay()
    }, 300)


  }

  ngAfterViewInit() {
    console.log("GamedisplayComponent::ngAfterViewInit")
    this.isDebug = window.location.search.indexOf("debug") !== -1
    this.resizeCanvas()
    this.setupCanvasContext()
    this.setCanvasColor()
    this._camera.scannerPaneCamera.setMiddleZoom()
  }

  private setupCanvasContext() {
    this.ctx = this.ctx || this.canvas.nativeElement.getContext("2d")
  }

  private setCanvasColor() {
    this.canvas.nativeElement.style.backgroundColor = "#000000" // Black
  }

  @HostListener('window:resize', ['$event'])
  private resizeCanvas() {
    setTimeout(() => {
      console.log("GameDisplayComponent::resizeCanvas()")
      this.canvas.nativeElement.width = document.body.clientWidth;
      this.canvas.nativeElement.height = document.body.clientHeight;
      console.log({w: this.canvas.nativeElement.width, h: this.canvas.nativeElement.height})
      this._camera.gameDisplayCamera.registerCanvasWidthHeight(
        this.canvas.nativeElement.offsetWidth,
        this.canvas.nativeElement.offsetHeight,
      )
    })
  }

  ngOnDestroy() {
    console.log("GamedisplayComponent::ngOnDestroy")
  }

  // Camera methods
  getCameraMode(): string {
    return this.cameraMode
  }

  canManualZoom(): boolean {
    return this.cameraMode === CAMERA_MODE_SHIP
  }
  canManualPan(): boolean {
    // TODO: Observer mode
    return false
  }

  setCameraModeShip() {
    this.cameraMode = CAMERA_MODE_SHIP
    this._camera.gameDisplayCamera.setZoomIndex(this.previousCameraZoomIndex)
  }

  setCameraModeScanner() {
    if(this.cameraMode === CAMERA_MODE_SHIP) {
      this.previousCameraZoomIndex = this._camera.gameDisplayCamera.getZoomIndex()
    }
    this.cameraMode = CAMERA_MODE_SCANNER
  }

  cycleCameraMode() {
    const mode = this.getCameraMode()
    if(mode === CAMERA_MODE_MAP) {
      return
    }
    if (mode === CAMERA_MODE_SHIP) {
      this.setCameraModeScanner()
      // this.previousCameraZoomIndex = this._camera.gameDisplayCamera.getZoomIndex()
    } else if (mode === CAMERA_MODE_SCANNER) {
      this.setCameraModeShip()
    }
  }

  toggleMap() {
    if(this.cameraMode !== CAMERA_MODE_MAP) {
      this.setModeMap()
    } else {
      this.closeMap()
    }
  }

  setModeMap(): void {
    // Save previous camera info for when map closes.
    this.previousCameraMode = this.getCameraMode()
    if(this.previousCameraMode === CAMERA_MODE_SHIP) {
      this.previousCameraZoomIndex = this._camera.gameDisplayCamera.getZoomIndex()
    }
    // Calculate position
    this.cameraMode = CAMERA_MODE_MAP
    const mapCenterX = Math.floor(this._api.frameData.map_config.x_unit_length / 2)
    const mapCenterY = Math.floor(this._api.frameData.map_config.y_unit_length / 2)
    this._camera.gameDisplayCamera.setPosition(mapCenterX, mapCenterY)

    // Calculate zoom to show full map
    const mapUnitsPerPxW = Math.floor(
      mapCenterX / (this._camera.gameDisplayCamera.canvasHalfWidth - 40))
    const mapUnitsPerPxH = Math.floor(
      mapCenterY / (this._camera.gameDisplayCamera.canvasHalfHeight - 40))
    const mapUnitsPerPxX = Math.max(mapUnitsPerPxW, mapUnitsPerPxH)
    this._camera.gameDisplayCamera.setZoom(mapUnitsPerPxX)
  }

  public closeMap() {
    if (this.previousCameraMode == CAMERA_MODE_SHIP) {
      this.setCameraModeShip()
    }
    else if (this.previousCameraMode == CAMERA_MODE_SCANNER) {
      this.setCameraModeScanner()
    }
    else {
      console.warn("could not select a camera profile after closing map.")
    }
  }


  @HostListener('document:keypress', ['$event'])
  private handleKeyboardEvent(event: KeyboardEvent) {
    if(this._pane.getInputIsFocused()) {
      return
    }
    const key = event.key.toLocaleLowerCase()
    console.log({gameKeystroke: key})
    switch (true) {
      case key === 'm':
        this.toggleMap()
        break
      case key === 'c':
        this.cycleCameraMode()
        break
    }
  }

  private registerMouseEventListener(): void {
    // Zoom camera
    window.addEventListener('wheel', event => {
      const zoomIn = event.deltaY < 0
      if(this._pane.mouseInPane()) {
        if(this._pane.mouseInScannerPane() && this._api.frameData.ship.scanner_online) {
          this._camera.scannerPaneCamera.adjustZoom(zoomIn)
        }
        return
      }
      if (this.canManualZoom()) {
        console.log("zoomingIn " + zoomIn)
        this._camera.gameDisplayCamera.adjustZoom(zoomIn)
      }
    })

    this.canvas.nativeElement.addEventListener('mouseover', () => {
      this.mouseInCanvas = true
    })

    // Pan camera
    this.canvas.nativeElement.addEventListener('mouseenter', ()=>{
      console.log("mouseenter")
      this.mouseInCanvas = true
    })
    this.canvas.nativeElement.addEventListener('mouseleave', event => {
      const canvasWidth = this.canvas.nativeElement.width
      const canvasHeight = this.canvas.nativeElement.height
      const eventXPos = event.clientX
      const eventYPos = event.clientY
      console.log("mouseleave")
      this.mouseClickDownInCanvas = false
      this.mouseInCanvas = false
      this.mousePanLastX = null
      this.mousePanLastY = null

    })
    this.canvas.nativeElement.addEventListener('mousedown', ()=>{
      this.mouseMovedWhileDown = false
      if(this.mouseInCanvas) {
        this.mouseClickDownInCanvas = true
      }
    })
    window.addEventListener('mouseup', (event) => {
      if(/*!this.mouseMovedWhileDown &&*/ this.mouseInCanvas && !this._pane.mouseInPane()) {
        this.handleMouseClickInCanvas(event)
      }
      this.mouseClickDownInCanvas = false
      this.mouseMovedWhileDown = false
      this.mousePanLastX = null
      this.mousePanLastY = null
    })
    window.addEventListener('mousemove', event => {
      this.mouseMovedWhileDown = true
      if(!this.canManualPan() || !this.mouseClickDownInCanvas || !this.mouseInCanvas) {
        return
      }
      else if(this.mousePanLastX === null || this.mousePanLastY === null) {
        this.mousePanLastX = event.screenX
        this.mousePanLastY = event.screenY
      }
      else {
        const cameraZoom = this._camera.gameDisplayCamera.getZoom()
        const scaledDeltaX = (this.mousePanLastX - event.screenX) * cameraZoom
        const scaledDeltaY = (this.mousePanLastY - event.screenY) * cameraZoom * -1
        this._camera.gameDisplayCamera.xPan(scaledDeltaX)
        this._camera.gameDisplayCamera.yPan(scaledDeltaY)
        this.mousePanLastX = event.screenX
        this.mousePanLastY = event.screenY
      }
    })
    console.log("Done registering all mouse events!")
  }

  private handleMouseClickInCanvas(event: any): void {
    console.log("handleMouseClickInCanvas")

    if(this._api.frameData === null) {
      return
    }
    const mouseCanvasX = event.clientX - this.canvas.nativeElement.offsetLeft
    const mouseCanvasY = event.clientY - this.canvas.nativeElement.offsetTop
    if(
      this.drawableObjects !== null
      && typeof this.drawableObjects.ships[0] !== 'undefined'
      && this.drawableObjects.ships[0].isSelf
    ) {
      const cameraMode = this.getCameraMode()
      let canvasBtnClicked = false
      if(cameraMode !== CAMERA_MODE_MAP) {
        const canvasBtnsToCheck = Object.keys(this.btnCanvasLocations)
        for(let i in canvasBtnsToCheck) {
          let bc:BoxCoords = this.btnCanvasLocations[canvasBtnsToCheck[i]]
          if(this._camera.boxesOverlap(
            bc,
            {x1:mouseCanvasX, x2:mouseCanvasX, y1:mouseCanvasY, y2:mouseCanvasY})
          ) {
            this.clickBtnClickAnimationFrame = 1
            this.clickBtnClickAnimationCanvasX = mouseCanvasX
            this.clickBtnClickAnimationCanvasY = mouseCanvasY
            this.handleBtnClick(canvasBtnsToCheck[i])
            canvasBtnClicked = true
            break
          }
        }
      }
      if(cameraMode !== CAMERA_MODE_MAP && !canvasBtnClicked && !this._api.frameData.ship.autopilot_program) {
        this.clickHeadingAdjAnimationFrame = 1
        this.clickHeadingAdjAnimationCanvasX = mouseCanvasX
        this.clickHeadingAdjAnimationCanvasY = mouseCanvasY
        this.handleMouseClickInCanvasHeadingAdjust(mouseCanvasX, mouseCanvasY)
      }
      else if (cameraMode == CAMERA_MODE_MAP) {
        this.handleMouseClickInCanvasDropWaypoint(cameraMode, mouseCanvasX, mouseCanvasY)
        if(this._api.frameData.ship.autopilot_program == 'lock_waypoint') {
          console.log("reclicking to lock heading to waypoint")
          setTimeout(() => {
            this.btnAutoPilotHeadingLockWaypoint()
          }, 15)
        }
      }

    }
  }

  private async handleMouseClickInCanvasHeadingAdjust(canvasClickX: number, canvasClickY: number) {
    const canvasClickPoint: PointCoord = {x: canvasClickX, y: canvasClickY}
    if(!this.drawableObjects.ships[0].isSelf) {
      return console.warn("could not handle heading adjust. ship0 != self")
    }
    const canvasShipPoint: PointCoord = this.drawableObjects.ships[0].canvasCoordCenter
    const heading = this._camera.gameDisplayCamera.getCanvasAngleBetween(canvasShipPoint, canvasClickPoint)
    await this._api.post(
      "/api/rooms/command",
      {command: "set_heading", heading},
    )
  }

  private async handleMouseClickInCanvasDropWaypoint(
    mode: string,
    canvasClickX: number,
    canvasClickY: number,
  ) {
    if (mode !== CAMERA_MODE_MAP) {
      return console.warn("handleMouseClickInCanvasDropWaypoint only runs in map mode")
    }
    const getCanvasDistanceBetweenCanvasCoords = (
      p1: PointCoord,
      p2: PointCoord
    ): number => {
      return Math.sqrt(
        Math.pow(p1.x - p2.x, 2)
        + Math.pow(p1.y - p2.y, 2)
      )
    }
    let minDist: number
    let minDistData: any
    const cameraPosition = this._camera.gameDisplayCamera.getPosition()
    for(let i in this._api.frameData.ore_mines) {
      let om = this._api.frameData.ore_mines[i]
      let omCanvasCoord = this._camera.gameDisplayCamera.mapCoordToCanvasCoord(
        {x: om.position_map_units_x, y: om.position_map_units_y},
        cameraPosition,
      )
      let canvasDistance = getCanvasDistanceBetweenCanvasCoords(
        omCanvasCoord, {x: canvasClickX, y: canvasClickY}
      )
      if(typeof minDist === 'undefined' || minDist > canvasDistance) {
        minDist = canvasDistance
        minDistData = om
      }
    }
    for(let i in this._api.frameData.space_stations) {
      let st = this._api.frameData.space_stations[i]
      let stCanvasCoord = this._camera.gameDisplayCamera.mapCoordToCanvasCoord(
        {x: st.position_map_units_x, y: st.position_map_units_y},
        cameraPosition,
      )
      let canvasDistance = getCanvasDistanceBetweenCanvasCoords(
        stCanvasCoord, {x: canvasClickX, y: canvasClickY}
      )
      if(typeof minDist === 'undefined' || minDist > canvasDistance) {
        minDist = canvasDistance
        minDistData = st
      }
    }
    if (minDist <  20) {
      if(this.wayPointUUID !== null && this.wayPointUUID === minDistData.uuid) {
        console.log("clearing waypoint")
        this.wayPointUUID = null
        this.wayPoint = null
        return
      } else {
        console.log("setting new waypoint")
        this.wayPointUUID = minDistData.uuid
        this.wayPoint = {
          x: minDistData.position_map_units_x,
          y: minDistData.position_map_units_y,
        }
      }
    }
  }

  private getCurrentTubeWeaponCount() {
    if(this.selectedPneumaticWeapon == MAGNET_MINE_SLUG) {
      return this._api.frameData.ship.magnet_mines_loaded
    } else if (this.selectedPneumaticWeapon == EMP_SLUG) {
      return this._api.frameData.ship.emps_loaded
    }
    return 0
  }

  public getHumanReadableCurrentTubeWeapon() {
    return this.selectedPneumaticWeapon.replace(/\_/g, " ").toLowerCase().split(' ').map((word: string)=>{
      return (word.charAt(0).toUpperCase() + word.slice(1));
    }).join(' ');
  }

  private clearCanvas(): void {
    this.ctx.beginPath()
    this.ctx.clearRect(0, 0, this._camera.gameDisplayCamera.canvasWidth * 2, this._camera.gameDisplayCamera.canvasHeight * 2) // *2 because of bug where corner is not cleared
  }

  private paintDisplay(): void {

    if (this._api.frameData === null) {
      window.requestAnimationFrame(this.paintDisplay.bind(this))
      return
    }
    this.clearCanvas()

    const camCoords = this._camera.gameDisplayCamera.getPosition()
    const cameraMode = this.getCameraMode()
    if(camCoords.x === null || camCoords.y === null) {
      this._camera.gameDisplayCamera.setPosition(
        this._api.frameData.ship.coord_x,
        this._api.frameData.ship.coord_y,
      )
    }

    if (cameraMode === CAMERA_MODE_SHIP) {
      this._camera.gameDisplayCamera.setPosition(
        this._api.frameData.ship.coord_x,
        this._api.frameData.ship.coord_y,
      )
    }
    else if (cameraMode === CAMERA_MODE_SCANNER) {
      this.previousCameraZoomIndex = this._camera.gameDisplayCamera.getZoomIndex()
      this._camera.gameDisplayCamera.setCameraPositionAndZoomForScannerMode(
        this._scanner.scannerTargetIDCursor,
      )
    }

    const drawableObjects: DrawableCanvasItems = this._camera.gameDisplayCamera.getDrawableCanvasObjects()
    this.drawableObjects = drawableObjects

    // Vision circles
    this._draw.drawVisionCircles(this.ctx, drawableObjects.visionCircles)

    this._draw.drawExplosionShockwaves(this.ctx, this._camera.gameDisplayCamera)

    // Draw Map boundary
    this._draw.drawMapBoundary(this.ctx, this._camera.gameDisplayCamera, drawableObjects.mapWall);

    // Add map features
    this._draw.drawSpaceStations(this.ctx, this._camera.gameDisplayCamera)
    this._draw.drawMiningLocations(this.ctx, this._camera.gameDisplayCamera)

    // Waypoint, if one is set
    if(this.wayPoint !== null) {
      this._draw.drawWaypoint(this.ctx, this._camera.gameDisplayCamera, this.wayPoint)
    }

    // expect smallest vision circle at end of array
    const lastIx = drawableObjects.visionCircles.length - 1
    if(lastIx > -1) {
      this._draw.drawVelocityAndHeadingLine(
        this.ctx,
        this._camera.gameDisplayCamera,
        drawableObjects.visionCircles[lastIx],
      )
    }

    if(
      this._api.frameData.ship.scanner_online &&
      (this._scanner.scannerTargetIDCursor !== null || this._api.frameData.ship.scanner_lock_target)
    ) {
      this._draw.drawLineToScannerCursor(
        this.ctx,
        this._camera.gameDisplayCamera,
        this._api.frameData.ship.scanner_lock_target ?this._api.frameData.ship.scanner_lock_target :this._scanner.scannerTargetIDCursor,
      );
    }

    this._draw.drawVisualFlameSmokeElements(
      this.ctx, this._camera.gameDisplayCamera,
      this._camera.getFlameSmokeElements()
    )
    this._draw.drawVisualVelocityElements(
      this.ctx, this._camera.gameDisplayCamera,
      this._camera.getVelocityTrailElements(),
    )

    this._draw.drawEMPTrailElements(
      this.ctx, this._camera.gameDisplayCamera,
      this._camera.getEMPTrailElements(),
    )

    // Ships
    for(let i in drawableObjects.ships) {
      this._draw.drawShip(
        this.ctx,
        this._camera.gameDisplayCamera,
        drawableObjects.ships[i],
        this._scanner.scannerTargetIDCursor,
        true,
      )
      if(drawableObjects.ships[i].visualEbeamFiring) {
        this._camera.addEBeamFiringEffectElement(
          drawableObjects.ships[i].HBNoseMapCoord
        )
      }
      if(drawableObjects.ships[i].engineLit && Math.random() < 0.33) {
        this._camera.addFlameSmokeElement(
          drawableObjects.ships[i].HBBottomCenterMapCoord,
          randomInt(3, 5)
        )
      }
    }
    // magnet mines
    for(let i in drawableObjects.magnetMines) {
      this._draw.drawMagnetMine(this.ctx, drawableObjects.magnetMines[i])
    }
    this._draw.drawMagnetMineTargetingLines(
      this.ctx,
      drawableObjects.magnetMineTargetingLines
    )
    // EMPs
    for(let i in drawableObjects.emps) {
      this._draw.drawEMP(this.ctx, drawableObjects.emps[i])
    }

    this._draw.drawExplosions(this.ctx, this._camera.gameDisplayCamera)
    this._draw.drawEMPBlasts(this.ctx, this._camera.gameDisplayCamera)

    this._draw.drawOreDepositEffect(this.ctx, this._camera.gameDisplayCamera)

    // E-Beams
    this._draw.drawEbeams(this.ctx, this._camera.gameDisplayCamera, drawableObjects.ebeamRays)
    this._draw.drawEBeamFiringEffectElements(
      this.ctx,
      this._camera.gameDisplayCamera,
      this._camera.getEBeamFiringEffectElements(),
    )

    this._draw.drawShipGravityBrakeEffectElements(
      this.ctx,
      this._camera.gameDisplayCamera,
      this._camera.getGravityBrakeShipEffectElements(),
    )

    // Corner overlays
    if(cameraMode !== CAMERA_MODE_MAP) {
      this._draw.drawTopLeftOverlay(this.ctx, cameraMode);
      this._draw.drawBottomRightOverlay(this.ctx, this._camera.gameDisplayCamera)
      if(!this.isDebug && this._api.frameData.ship.alive) {
        this._draw.drawTopRightOverlay(this.ctx, this._camera.gameDisplayCamera, this.wayPoint)
      }
    }
    // Front center and alerts
    this._draw.drawFrontAndCenterAlerts(this.ctx, this._camera.gameDisplayCamera)

    // Click feedback
    if(this.clickHeadingAdjAnimationFrame) {
      this.ctx.beginPath()
      this.ctx.strokeStyle = "#7d00a3"
      this.ctx.lineWidth = 3
      this.ctx.arc(
        this.clickHeadingAdjAnimationCanvasX,
        this.clickHeadingAdjAnimationCanvasY,
        this.clickHeadingAdjAnimationFrame * 2.5,
        0,
        TWO_PI,
      )
      this.ctx.stroke()
      this.clickHeadingAdjAnimationFrame++
      if (this.clickHeadingAdjAnimationFrame > 10) {
        this.clickHeadingAdjAnimationFrame = null
      }
    }
    if(this.clickBtnClickAnimationFrame) {
      this.ctx.beginPath()
      this.ctx.strokeStyle = "#00ff00"
      this.ctx.lineWidth = 3
      this.ctx.arc(
        this.clickBtnClickAnimationCanvasX,
        this.clickBtnClickAnimationCanvasY,
        this.clickBtnClickAnimationFrame * 2.5,
        0,
        TWO_PI,
      )
      this.ctx.stroke()
      this.clickBtnClickAnimationFrame++
      if (this.clickBtnClickAnimationFrame > 10) {
        this.clickBtnClickAnimationFrame = null
      }
    }

    if(this.isDebug) {
      this.paintDebugData();
    }
    if(this.cameraMode !== CAMERA_MODE_MAP) {
      this.paintButtons()
    }
    this._sound.runSoundFXEngine();
    window.requestAnimationFrame(this.paintDisplay.bind(this))
  }

  private getButtonSizingData(): ButtonSizing {
    const canvasDim = Math.min(
      this._camera.gameDisplayCamera.canvasHeight,
      this._camera.gameDisplayCamera.canvasWidth,
    )
    if(this._camera.gameDisplayCamera.canvasWidth >= 650 && this._camera.gameDisplayCamera.canvasHeight >= 450) {
      // "Larger" screen configuration
      return {
        cornerOffset: 15,
        fontSize: 23,
        xLenMenu: 135,
        xLenEngineMenu: 125,
        xLenAutopilotMenu: 150,
        xLenScannerC1Menu: 108,
        xLenScannerC2Menu: 68,
        xLenEMEBeamMenu: 95,
        xLenTorpedoC1Menu: 120,
        xLenTorpedoC2Menu: 68,
        xLenUtilitiesMenu: 150,
        yLen: 29,
        xGap: 10,
        yGap: 10,
      }
    } else {
      // "Smaller" screen configuration
      return {
        cornerOffset: 5,
        fontSize: 16,
        xLenMenu: 95,
        xLenEngineMenu: 85,
        xLenAutopilotMenu: 105,
        xLenScannerC1Menu: 75,
        xLenScannerC2Menu: 47,
        xLenEMEBeamMenu: 65,
        xLenTorpedoC1Menu: 87,
        xLenTorpedoC2Menu: 49,
        xLenUtilitiesMenu: 107,
        yLen: 20,
        xGap: 6,
        yGap: 5,
      }
    }
  }

  private paintButtons() {
    if(this._api.frameData.ship.alive) {
      const sizing = this.getButtonSizingData()
      this.paintLeftCornerButtons(sizing)
    } else {
      this.btnCanvasLocations = {}
    }
  }

  private getAndUpdateBtnBoarderWidth(btnName: string): number {
    if(this.clickBtnBoarderAnimationFrame && btnName == this.clickBtnBoarderAnimationButtonName){
      const border = 2 + this.clickBtnBoarderAnimationFrame * 0.65
      if(this.clickBtnBoarderAnimationFrame++ > 15) {
        this.clickBtnBoarderAnimationFrame = null
        this.clickBtnBoarderAnimationButtonName = null
      }
      console.log({border})
      return border
    }
    return 2// Default
  }

  private paintLeftCornerButtons(sizing: ButtonSizing) {
    const ship = this._api.frameData.ship
    const canvasHeight = this._camera.gameDisplayCamera.canvasHeight
    const cornerOffset = 15
    let col1YOffset = 0, col2YOffset = 0, col3YOffset = 0
    const textLeftBuffer = 5
    let x1: number, x2: number, y1: number, y2: number
    const alpha = getRandomFloat(0.40, 0.55)
    const btnColorWhite = `rgb(255, 255, 255, ${alpha})`
    const btnColorGray = `rgb(180, 180, 180, ${alpha})`
    const btnColorGreen = `rgb(0, 255, 17, ${alpha})`
    const btnColorRed = `rgb(255, 140, 140, ${alpha})`
    const btnColorBlack = "#000000"

    this.ctx.textAlign = "left";
    this.ctx.textBaseline = "bottom"

    // Engine Menu
    x1 = sizing.cornerOffset
    x2 = x1 + sizing.xLenMenu
    y2 = canvasHeight - sizing.cornerOffset - col1YOffset
    y1 = y2 - sizing.yLen
    this.btnCanvasLocations.engineMenu = {x1, x2, y1, y2}
    this.ctx.beginPath()
    const engineMenuSelected = this.activeBtnGroup === ButtonGroup.ENGINE
    const engineOnline = ship.engine_online || ship.engine_starting
    this.ctx.strokeStyle = engineMenuSelected? btnColorGreen: btnColorWhite
    this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("engineMenu")
    this.ctx.strokeRect(x1, y1, sizing.xLenMenu, sizing.yLen)
    if(engineMenuSelected) {
      // Engine Menu selected
      this.ctx.beginPath()
      this.ctx.fillStyle = btnColorWhite
      this.ctx.fillRect(x1, y1, sizing.xLenMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = btnColorBlack
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("ENGINE", x1 + textLeftBuffer, y2)
      // Engine Column 2 buttons
      // BOOST
      let enabled = ship.engine_lit
      let disabled: boolean, fullyDisabled: boolean
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenEngineMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.engineBoost = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = enabled? btnColorWhite: btnColorGray
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("engineBoost")
      this.ctx.strokeRect(x1, y1, sizing.xLenEngineMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = enabled? btnColorWhite: btnColorGray
      this.ctx.font = `${enabled?"":"italic "}bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("BOOST", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // IGNITE
      enabled = ship.engine_lit
      disabled = !ship.engine_online || ship.engine_lit
      fullyDisabled = !ship.engine_online
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenEngineMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.engineIgnite = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = fullyDisabled? btnColorGray: (enabled? btnColorGreen: btnColorWhite)
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("engineIgnite")
      this.ctx.strokeRect(x1, y1, sizing.xLenEngineMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = fullyDisabled? btnColorGray: (enabled? btnColorGreen: btnColorWhite)
      this.ctx.font = `${disabled?"italic ":""}bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("IGNITE", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // IDLE
      enabled = !ship.engine_lit
      disabled = !ship.engine_online
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenEngineMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.engineIdle = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = disabled? btnColorGray: enabled?btnColorGreen: btnColorWhite
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("engineIdle")
      this.ctx.strokeRect(x1, y1, sizing.xLenEngineMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = disabled? btnColorGray: enabled?btnColorGreen: btnColorWhite
      this.ctx.font = `${disabled?"italic ":""}bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("IDLE", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // SHUTDOWN
      enabled = ship.engine_online
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenEngineMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.engineShutdown = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = enabled? btnColorWhite: btnColorGray
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("engineShutdown")
      this.ctx.strokeRect(x1, y1, sizing.xLenEngineMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = enabled? btnColorWhite: btnColorGray
      this.ctx.font = `${enabled?"":"italic "}bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("SHUTDOWN", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // STARTUP
      enabled = ship.engine_online || ship.engine_starting
      disabled = ship.engine_starting
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenEngineMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.engineStartup = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = enabled? btnColorGreen: btnColorWhite
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("engineStartup")
      this.ctx.strokeRect(x1, y1, sizing.xLenEngineMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = enabled? btnColorGreen: btnColorWhite
      this.ctx.font = `${disabled?"italic ":""}bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("STARTUP", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)

      // Aestetic Outline
      this.ctx.beginPath()
      this.ctx.strokeStyle = btnColorGreen
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("engineMenu")
      this.ctx.moveTo(
        this.btnCanvasLocations.engineMenu.x2,
        this.btnCanvasLocations.engineMenu.y1)
      this.ctx.lineTo(
        this.btnCanvasLocations.engineMenu.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.engineMenu.y1)
      this.ctx.lineTo(
        this.btnCanvasLocations.engineMenu.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.engineStartup.y1 - sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.engineStartup.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.engineStartup.y1 - sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.engineStartup.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.engineBoost.y2 + sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.engineStartup.x1 - sizing.xGap / 2,
        this.btnCanvasLocations.engineBoost.y2 + sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.engineMenu.x2,
        this.btnCanvasLocations.engineMenu.y2)
      this.ctx.stroke()


    } else {
      this.ctx.beginPath()
      this.ctx.fillStyle = engineOnline? btnColorGreen: btnColorWhite
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("ENGINE", x1 + textLeftBuffer, y2)
      delete this.btnCanvasLocations.engineStartup
      delete this.btnCanvasLocations.engineShutdown
      delete this.btnCanvasLocations.engineIdle
      delete this.btnCanvasLocations.engineIgnite
      delete this.btnCanvasLocations.engineBoost
    }
    col1YOffset += (sizing.yGap + sizing.yLen)

    // Autopilot Menu
    x1 = sizing.cornerOffset
    x2 = x1 + sizing.xLenMenu
    y2 = canvasHeight - sizing.cornerOffset - col1YOffset
    y1 = y2 - sizing.yLen
    this.btnCanvasLocations.autoPilotMenu = {x1, x2, y1, y2}
    this.ctx.beginPath()
    this.ctx.strokeStyle = this.activeBtnGroup === ButtonGroup.AUTOPILOT? btnColorGreen: btnColorWhite
    this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("autoPilotMenu")
    this.ctx.strokeRect(x1, y1, sizing.xLenMenu, sizing.yLen)
    if(this.activeBtnGroup === ButtonGroup.AUTOPILOT) {
      this.ctx.beginPath()
      this.ctx.fillStyle = btnColorWhite
      this.ctx.fillRect(x1, y1, sizing.xLenMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = btnColorBlack
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("AUTOPILOT", x1 + textLeftBuffer, y2)
      // Autopilot Column 2 buttons
      // Lock Retrograde
      let active = ship.autopilot_program == "lock_retrograde" || ship.autopilot_program == "position_hold"
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenAutopilotMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.autoPilotRetrograde = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = active? btnColorGreen: btnColorWhite
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("autoPilotRetrograde")
      this.ctx.strokeRect(x1, y1, sizing.xLenAutopilotMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = active? btnColorGreen: btnColorWhite
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("RETROGRADE", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // Lock Prograde
      active = ship.autopilot_program == "lock_prograde"
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenAutopilotMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.autoPilotPrograde = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = active? btnColorGreen: btnColorWhite
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("autoPilotPrograde")
      this.ctx.strokeRect(x1, y1, sizing.xLenAutopilotMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = active? btnColorGreen: btnColorWhite
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("PROGRADE", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // Lock Waypoint
      active = ship.autopilot_program == "lock_waypoint"
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenAutopilotMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.autoPilotWaypoint = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = active? btnColorGreen: btnColorWhite
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("autoPilotWaypoint")
      this.ctx.strokeRect(x1, y1, sizing.xLenAutopilotMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = active? btnColorGreen: btnColorWhite
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("WAYPOINT", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // Lock Target
      active = ship.autopilot_program == "lock_target"
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenAutopilotMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.autoPilotTarget = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = active? btnColorGreen: btnColorWhite
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("autoPilotTarget")
      this.ctx.strokeRect(x1, y1, sizing.xLenAutopilotMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = active? btnColorGreen: btnColorWhite
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("TARGET", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // HALT
      active = ship.autopilot_program == "position_hold"
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenAutopilotMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.autoPilotHalt = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = active? btnColorGreen: btnColorWhite
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("autoPilotHalt")
      this.ctx.strokeRect(x1, y1, sizing.xLenAutopilotMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = active? btnColorGreen: btnColorWhite
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("HALT", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // DISABLE
      let enabled = ship.autopilot_program !== null
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenAutopilotMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.autoPilotDisabled = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = enabled? btnColorWhite: btnColorGray
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("autoPilotDisabled")
      this.ctx.strokeRect(x1, y1, sizing.xLenAutopilotMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = enabled? btnColorWhite: btnColorGray
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("DISABLE", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)

      // Aestetic Outline
      this.ctx.beginPath()
      this.ctx.strokeStyle = btnColorGreen
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("autoPilotMenu")
      this.ctx.moveTo(
        this.btnCanvasLocations.autoPilotMenu.x2,
        this.btnCanvasLocations.autoPilotMenu.y1)
      this.ctx.lineTo(
        this.btnCanvasLocations.autoPilotMenu.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.autoPilotMenu.y1)
      this.ctx.lineTo(
        this.btnCanvasLocations.autoPilotDisabled.x1 - sizing.xGap / 2,
        this.btnCanvasLocations.autoPilotDisabled.y1 - sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.autoPilotDisabled.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.autoPilotDisabled.y1 - sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.autoPilotDisabled.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.autoPilotRetrograde.y2 + sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.autoPilotDisabled.x1 - sizing.xGap / 2,
        this.btnCanvasLocations.autoPilotRetrograde.y2 + sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.autoPilotMenu.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.autoPilotMenu.y2)
      this.ctx.lineTo(
        this.btnCanvasLocations.autoPilotMenu.x2,
        this.btnCanvasLocations.autoPilotMenu.y2)
      this.ctx.stroke()

    } else {
      this.ctx.beginPath()
      this.ctx.fillStyle = ship.autopilot_program !== null? btnColorGreen: btnColorWhite
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("AUTOPILOT", x1 + textLeftBuffer, y2)
      delete this.btnCanvasLocations.autoPilotRetrograde
      delete this.btnCanvasLocations.autoPilotPrograde
      delete this.btnCanvasLocations.autoPilotWaypoint
      delete this.btnCanvasLocations.autoPilotTarget
      delete this.btnCanvasLocations.autoPilotHalt
      delete this.btnCanvasLocations.autoPilotDisabled
    }
    col1YOffset += (sizing.yGap + sizing.yLen)

    // Scanner Menu
    x1 = sizing.cornerOffset
    x2 = x1 + sizing.xLenMenu
    y2 = canvasHeight - sizing.cornerOffset - col1YOffset
    y1 = y2 - sizing.yLen
    this.btnCanvasLocations.scannerMenuBtn = {x1, x2, y1, y2}
    this.ctx.beginPath()
    this.ctx.strokeStyle = this.activeBtnGroup === ButtonGroup.SCANNER? btnColorGreen: btnColorWhite
    this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("scannerMenuBtn")
    this.ctx.strokeRect(x1, y1, sizing.xLenMenu, sizing.yLen)
    if(this.activeBtnGroup === ButtonGroup.SCANNER) {
      this.ctx.beginPath()
      this.ctx.fillStyle = btnColorWhite
      this.ctx.fillRect(x1, y1, sizing.xLenMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = btnColorBlack
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("SCANNER", x1 + textLeftBuffer, y2)
      // Scanner Column 2 buttons
      // IR
      let disabled = !ship.scanner_online
      let active = ship.scanner_online && ship.scanner_mode === "ir"
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenScannerC1Menu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.scannerIRBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = disabled ? btnColorGray : (active? btnColorGreen: btnColorWhite)
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("scannerIRBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenScannerC1Menu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = disabled ? btnColorGray : (active? btnColorGreen: btnColorWhite)
      this.ctx.font = `${disabled?"italic ":""}bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("THERMAL", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // RADAR
      disabled = !ship.scanner_online
      active = ship.scanner_online && ship.scanner_mode === "radar"
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenScannerC1Menu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.scannerRadarBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = disabled ? btnColorGray : (active? btnColorGreen: btnColorWhite)
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("scannerRadarBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenScannerC1Menu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = disabled ? btnColorGray : (active? btnColorGreen: btnColorWhite)
      this.ctx.font = `${disabled?"italic ":""}bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("RADAR", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // Stop
      disabled = !ship.scanner_online
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenScannerC1Menu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.scannerStopBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = disabled ? btnColorGray : btnColorWhite
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("scannerStopBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenScannerC1Menu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = disabled ? btnColorGray :btnColorWhite
      this.ctx.font = `${disabled?"italic ":""}bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("DISABLE", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // Start
      disabled = ship.scanner_starting
      active = ship.scanner_online
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenScannerC1Menu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.scannerStartBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = disabled ? btnColorGray : (active? btnColorGreen: btnColorWhite)
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("scannerStartBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenScannerC1Menu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = disabled ? btnColorGray : (active? btnColorGreen: btnColorWhite)
      this.ctx.font = `${disabled?"italic ":""}bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("START", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // Scanner Column 3 buttons
      // Lock
      disabled = !ship.scanner_online || !ship.scanner_ship_data.length
      active = ship.scanner_locked || ship.scanner_locking
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xLenScannerC1Menu + sizing.xGap + sizing.xGap
      x2 = x1 + sizing.xLenScannerC2Menu
      y2 = canvasHeight - sizing.cornerOffset - col3YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.scannerLockBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = disabled ? btnColorGray : (active? btnColorRed: btnColorWhite)
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("scannerLockBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenScannerC2Menu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = disabled ? btnColorGray : (active? btnColorRed: btnColorWhite)
      this.ctx.font = `${disabled?"italic ":""}bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("LOCK", x1 + textLeftBuffer, y2)
      col3YOffset += (sizing.yGap + sizing.yLen)
      // Down Arrow
      disabled = !ship.scanner_online || !ship.scanner_ship_data.length
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xLenScannerC1Menu + sizing.xGap + sizing.xGap
      x2 = x1 + sizing.xLenScannerC2Menu
      y2 = canvasHeight - sizing.cornerOffset - col3YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.scannerDownArrowBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = disabled ? btnColorGray : btnColorGreen
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("scannerDownArrowBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenScannerC2Menu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = disabled ? btnColorGray : btnColorGreen
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("PREV", x1 + textLeftBuffer, y2)
      col3YOffset += (sizing.yGap + sizing.yLen)
      // UP Arrow
      disabled = !ship.scanner_online || !ship.scanner_ship_data.length
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xLenScannerC1Menu + sizing.xGap + sizing.xGap
      x2 = x1 + sizing.xLenScannerC2Menu
      y2 = canvasHeight - sizing.cornerOffset - col3YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.scannerUpArrowBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = disabled ? btnColorGray : btnColorGreen
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("scannerUpArrowBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenScannerC2Menu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = disabled ? btnColorGray : btnColorGreen
      this.ctx.font = `${disabled? "italic ": ""} bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("NEXT", x1 + textLeftBuffer, y2)
      col3YOffset += (sizing.yGap + sizing.yLen)

      // Aestetic Outline
      this.ctx.beginPath()
      this.ctx.strokeStyle = btnColorGreen
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("scannerMenuBtn")
      this.ctx.moveTo(
        this.btnCanvasLocations.scannerMenuBtn.x2,
        this.btnCanvasLocations.scannerMenuBtn.y1)
      this.ctx.lineTo(
        this.btnCanvasLocations.scannerMenuBtn.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.scannerMenuBtn.y1)
      this.ctx.lineTo(
        this.btnCanvasLocations.scannerStartBtn.x1 - sizing.xGap / 2,
        this.btnCanvasLocations.scannerStartBtn.y1 - sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.scannerStartBtn.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.scannerStartBtn.y1 - sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.scannerStartBtn.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.scannerStartBtn.y2 + sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.scannerUpArrowBtn.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.scannerUpArrowBtn.y1 - sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.scannerUpArrowBtn.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.scannerLockBtn.y2 + sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.scannerStartBtn.x1 - sizing.xGap / 2,
        this.btnCanvasLocations.scannerLockBtn.y2 + sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.scannerMenuBtn.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.scannerMenuBtn.y2)
      this.ctx.lineTo(
        this.btnCanvasLocations.scannerMenuBtn.x2,
        this.btnCanvasLocations.scannerMenuBtn.y2)
      this.ctx.stroke()

    } else {
      this.ctx.beginPath()
      this.ctx.fillStyle = ship.scanner_online || ship.scanner_starting? btnColorGreen: btnColorWhite
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("SCANNER", x1 + textLeftBuffer, y2)
      delete this.btnCanvasLocations.scannerStartBtn
      delete this.btnCanvasLocations.scannerStopBtn
      delete this.btnCanvasLocations.scannerRadarBtn
      delete this.btnCanvasLocations.scannerIRBtn
      delete this.btnCanvasLocations.scannerUpArrowBtn
      delete this.btnCanvasLocations.scannerDownArrowBtn
      delete this.btnCanvasLocations.scannerLockBtn
    }
    col1YOffset += (sizing.yGap + sizing.yLen)

    // Electromagnetic Energy Beam Menu
    x1 = sizing.cornerOffset
    x2 = x1 + sizing.xLenMenu
    y2 = canvasHeight - sizing.cornerOffset - col1YOffset
    y1 = y2 - sizing.yLen
    this.btnCanvasLocations.EMEBeamMenuBtn = {x1, x2, y1, y2}
    this.ctx.beginPath()
    this.ctx.strokeStyle = this.activeBtnGroup === ButtonGroup.EMEBEAM? btnColorGreen: btnColorWhite
    this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("EMEBeamMenuBtn")
    this.ctx.strokeRect(x1, y1, sizing.xLenMenu, sizing.yLen)
    if(this.activeBtnGroup === ButtonGroup.EMEBEAM) {
      this.ctx.beginPath()
      this.ctx.fillStyle = btnColorWhite
      this.ctx.fillRect(x1, y1, sizing.xLenMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = btnColorBlack
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("EME-BEAM", x1 + textLeftBuffer, y2)
      // EME Beam Column 2 buttons
      // FIRE
      let disabled = !ship.ebeam_can_fire
      let active: boolean
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenEMEBeamMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.EMEBeamFireBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = disabled ? btnColorGray: btnColorRed
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("EMEBeamFireBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenEMEBeamMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = disabled ? btnColorGray: btnColorRed
      this.ctx.font = `${disabled?"italic ":""}bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("FIRE", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // CHARGE
      active = ship.ebeam_charging
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenEMEBeamMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.EMEBeamChargeBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = (active? btnColorGreen: btnColorWhite)
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("EMEBeamChargeBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenEMEBeamMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = (active? btnColorGreen: btnColorWhite)
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("CHARGE", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // PAUSE
      disabled = !ship.ebeam_charging
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenEMEBeamMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.EMEBeamPauseBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = (disabled? btnColorGray: btnColorWhite)
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("EMEBeamPauseBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenEMEBeamMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = (disabled? btnColorGray: btnColorWhite)
      this.ctx.font = `${disabled?"italic ":""}bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("PAUSE", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)

      // Aestetic Outline
      this.ctx.beginPath()
      this.ctx.strokeStyle = btnColorGreen
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("EMEBeamMenuBtn")
      this.ctx.moveTo(
        this.btnCanvasLocations.EMEBeamMenuBtn.x2,
        this.btnCanvasLocations.EMEBeamMenuBtn.y1)
      this.ctx.lineTo(
        this.btnCanvasLocations.EMEBeamMenuBtn.x2 + sizing.xGap,
        this.btnCanvasLocations.EMEBeamMenuBtn.y1)
      this.ctx.lineTo(
        this.btnCanvasLocations.EMEBeamPauseBtn.x1,
      this.btnCanvasLocations.EMEBeamPauseBtn.y1 - sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.EMEBeamPauseBtn.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.EMEBeamPauseBtn.y1 - sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.EMEBeamPauseBtn.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.EMEBeamFireBtn.y2 + sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.EMEBeamPauseBtn.x1 - sizing.xGap / 2,
        this.btnCanvasLocations.EMEBeamFireBtn.y2 + sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.EMEBeamPauseBtn.x1 - sizing.xGap / 2,
        this.btnCanvasLocations.EMEBeamMenuBtn.y2)
      this.ctx.lineTo(
        this.btnCanvasLocations.EMEBeamMenuBtn.x2,
        this.btnCanvasLocations.EMEBeamMenuBtn.y2)
      this.ctx.stroke()

    } else {
      this.ctx.beginPath()
      this.ctx.fillStyle = ship.ebeam_can_fire || ship.ebeam_charging? btnColorGreen: btnColorWhite
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("EME-BEAM", x1 + textLeftBuffer, y2)
      delete this.btnCanvasLocations.EMEBeamChargeBtn
      delete this.btnCanvasLocations.EMEBeamPauseBtn
      delete this.btnCanvasLocations.EMEBeamFireBtn
    }
    col1YOffset += (sizing.yGap + sizing.yLen)

    // Torpedo Menu
    x1 = sizing.cornerOffset
    x2 = x1 + sizing.xLenMenu
    y2 = canvasHeight - sizing.cornerOffset - col1YOffset
    y1 = y2 - sizing.yLen
    this.btnCanvasLocations.torpedoMenuBtn = {x1, x2, y1, y2}
    this.ctx.beginPath()
    this.ctx.strokeStyle = this.activeBtnGroup === ButtonGroup.TORPEDO? btnColorGreen: btnColorWhite
    this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("torpedoMenuBtn")
    this.ctx.strokeRect(x1, y1, sizing.xLenMenu, sizing.yLen)
    if(this.activeBtnGroup === ButtonGroup.TORPEDO) {
      this.ctx.beginPath()
      this.ctx.fillStyle = btnColorWhite
      this.ctx.fillRect(x1, y1, sizing.xLenMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = btnColorBlack
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("TORPEDOS", x1 + textLeftBuffer, y2)
      // TORPEDO Column 2 buttons
      // EMP Selector
      let active = this.selectedPneumaticWeapon == EMP_SLUG
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenTorpedoC1Menu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.torpedoMenuSelEMPBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = active? btnColorGreen: btnColorWhite
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("torpedoMenuSelEMPBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenTorpedoC1Menu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = active? btnColorGreen: btnColorWhite
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("  EMP", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // EMP Selector
      active = this.selectedPneumaticWeapon == MAGNET_MINE_SLUG
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenTorpedoC1Menu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.torpedoMenuSelMagnetMineBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = active? btnColorGreen: btnColorWhite
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("torpedoMenuSelMagnetMineBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenTorpedoC1Menu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = active? btnColorGreen: btnColorWhite
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("MAG-MINE", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)

      // Torpedo Column 3 buttons
      // FIRE
      let disabled = this.getCurrentTubeWeaponCount() == 0
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xLenTorpedoC1Menu + sizing.xGap + sizing.xGap
      x2 = x1 + sizing.xLenTorpedoC2Menu
      y2 = canvasHeight - sizing.cornerOffset - col3YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.torpedoFireBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = disabled? btnColorGray: btnColorRed
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("torpedoFireBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenTorpedoC2Menu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = disabled? btnColorGray: btnColorRed
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("FIRE", x1 + textLeftBuffer, y2)
      col3YOffset += (sizing.yGap + sizing.yLen)
      // Down Arrow
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xLenTorpedoC1Menu + sizing.xGap + sizing.xGap
      x2 = x1 + sizing.xLenTorpedoC2Menu
      y2 = canvasHeight - sizing.cornerOffset - col3YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.torpedoDownArrowBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = btnColorWhite
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("torpedoDownArrowBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenTorpedoC2Menu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = btnColorWhite
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("DECR", x1 + textLeftBuffer, y2)
      col3YOffset += (sizing.yGap + sizing.yLen)
      // Up Arrow
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xLenTorpedoC1Menu + sizing.xGap + sizing.xGap
      x2 = x1 + sizing.xLenTorpedoC2Menu
      y2 = canvasHeight - sizing.cornerOffset - col3YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.torpedoUpArrowBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = btnColorWhite
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("torpedoUpArrowBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenTorpedoC2Menu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = btnColorWhite
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("INCR", x1 + textLeftBuffer, y2)
      col3YOffset += (sizing.yGap + sizing.yLen)

      // Aestetic Outline
      this.ctx.beginPath()
      this.ctx.strokeStyle = btnColorGreen
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("torpedoMenuBtn")
      this.ctx.moveTo(
        this.btnCanvasLocations.torpedoMenuBtn.x2,
        this.btnCanvasLocations.torpedoMenuBtn.y1)
      this.ctx.lineTo(
        this.btnCanvasLocations.torpedoMenuBtn.x2 + sizing.xGap,
        this.btnCanvasLocations.torpedoMenuBtn.y1)
      this.ctx.lineTo(
        this.btnCanvasLocations.torpedoMenuSelMagnetMineBtn.x1,
        this.btnCanvasLocations.torpedoMenuSelMagnetMineBtn.y1 - sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.torpedoMenuSelMagnetMineBtn.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.torpedoMenuSelMagnetMineBtn.y1 - sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.torpedoUpArrowBtn.x1 - sizing.xGap / 2,
        this.btnCanvasLocations.torpedoUpArrowBtn.y1 - sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.torpedoUpArrowBtn.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.torpedoUpArrowBtn.y1 - sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.torpedoUpArrowBtn.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.torpedoFireBtn.y2 + sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.torpedoMenuSelEMPBtn.x1 - sizing.xGap / 2,
        this.btnCanvasLocations.torpedoMenuSelEMPBtn.y2 + sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.torpedoMenuBtn.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.torpedoMenuBtn.y2)
      this.ctx.lineTo(
        this.btnCanvasLocations.torpedoMenuBtn.x2,
        this.btnCanvasLocations.torpedoMenuBtn.y2)
      this.ctx.stroke()

    } else {
      this.ctx.beginPath()
      this.ctx.fillStyle = btnColorWhite
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("TORPEDOS", x1 + textLeftBuffer, y2)
      delete this.btnCanvasLocations.torpedoFireBtn
      delete this.btnCanvasLocations.torpedoDownArrowBtn
      delete this.btnCanvasLocations.torpedoUpArrowBtn
      delete this.btnCanvasLocations.torpedoMenuSelMagnetMineBtn
      delete this.btnCanvasLocations.torpedoMenuSelEMPBtn
    }
    col1YOffset += (sizing.yGap + sizing.yLen)

    // Utilities Menu
    x1 = sizing.cornerOffset
    x2 = x1 + sizing.xLenMenu
    y2 = canvasHeight - sizing.cornerOffset - col1YOffset
    y1 = y2 - sizing.yLen
    this.btnCanvasLocations.utilitiesMenuBtn = {x1, x2, y1, y2}
    this.ctx.beginPath()
    this.ctx.strokeStyle = this.activeBtnGroup === ButtonGroup.UTILITIES? btnColorGreen: btnColorWhite
    this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("utilitiesMenuBtn")
    this.ctx.strokeRect(x1, y1, sizing.xLenMenu, sizing.yLen)
    if(this.activeBtnGroup === ButtonGroup.UTILITIES) {
      this.ctx.beginPath()
      this.ctx.fillStyle = btnColorWhite
      this.ctx.fillRect(x1, y1, sizing.xLenMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = btnColorBlack
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("UTILITIES", x1 + textLeftBuffer, y2)
      // UTILITIES Column 2 buttons
      // Gravity Brake
      let active = ship.gravity_brake_deployed
      let disabled =  ship.gravity_brake_retracting || ship.gravity_brake_extending
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenUtilitiesMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.gravityBrakeBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = disabled ? btnColorGray: (active? btnColorGreen: btnColorWhite)
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("gravityBrakeBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenUtilitiesMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = disabled ? btnColorGray: (active? btnColorGreen: btnColorWhite)
      this.ctx.font = `${disabled?"italic ":""}bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("GRAV BRAKE", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // ORE DRILL
      active = ship.mining_ore
      disabled =  !(ship.cargo_ore_mass_kg < ship.cargo_ore_mass_capacity_kg) || ship.parked_at_ore_mine === null
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenUtilitiesMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.oreMineBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = disabled ? btnColorGray: (active? btnColorGreen: btnColorWhite)
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("oreMineBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenUtilitiesMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = disabled ? btnColorGray: (active? btnColorGreen: btnColorWhite)
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("ORE DRILL", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)
      // Auxilary Power
      active = ship.apu_online
      disabled =  ship.apu_starting
      x1 = sizing.cornerOffset + sizing.xLenMenu + sizing.xGap
      x2 = x1 + sizing.xLenUtilitiesMenu
      y2 = canvasHeight - sizing.cornerOffset - col2YOffset
      y1 = y2 - sizing.yLen
      this.btnCanvasLocations.auxiliaryPowerBtn = {x1, x2, y1, y2}
      this.ctx.beginPath()
      this.ctx.strokeStyle = disabled ? btnColorGray: (active? btnColorGreen: btnColorWhite)
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("auxiliaryPowerBtn")
      this.ctx.strokeRect(x1, y1, sizing.xLenUtilitiesMenu, sizing.yLen)
      this.ctx.beginPath()
      this.ctx.fillStyle = disabled ? btnColorGray: (active? btnColorGreen: btnColorWhite)
      this.ctx.font = `${disabled?"italic ":""}bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("AUX POWER", x1 + textLeftBuffer, y2)
      col2YOffset += (sizing.yGap + sizing.yLen)

      // Aestetic Outline
      this.ctx.beginPath()
      this.ctx.strokeStyle = btnColorGreen
      this.ctx.lineWidth = this.getAndUpdateBtnBoarderWidth("utilitiesMenuBtn")
      this.ctx.moveTo(
        this.btnCanvasLocations.utilitiesMenuBtn.x2,
        this.btnCanvasLocations.utilitiesMenuBtn.y1)
      this.ctx.lineTo(
        this.btnCanvasLocations.utilitiesMenuBtn.x2 + sizing.xGap,
        this.btnCanvasLocations.utilitiesMenuBtn.y1)
      this.ctx.lineTo(
        this.btnCanvasLocations.auxiliaryPowerBtn.x1,
        this.btnCanvasLocations.auxiliaryPowerBtn.y1 - sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.auxiliaryPowerBtn.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.auxiliaryPowerBtn.y1 - sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.gravityBrakeBtn.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.gravityBrakeBtn.y2 + sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.gravityBrakeBtn.x1 - sizing.xGap / 2,
        this.btnCanvasLocations.gravityBrakeBtn.y2 + sizing.yGap / 2)
      this.ctx.lineTo(
        this.btnCanvasLocations.utilitiesMenuBtn.x2 + sizing.xGap / 2,
        this.btnCanvasLocations.utilitiesMenuBtn.y2)
      this.ctx.lineTo(
        this.btnCanvasLocations.utilitiesMenuBtn.x2,
        this.btnCanvasLocations.utilitiesMenuBtn.y2)
      this.ctx.stroke()

    } else {
      this.ctx.beginPath()
      this.ctx.fillStyle = ship.mining_ore || ship.gravity_brake_position != 0 || ship.apu_online || ship.apu_starting? btnColorGreen: btnColorWhite
      this.ctx.font = `bold ${sizing.fontSize}px courier new`
      this.ctx.fillText("UTILITIES", x1 + textLeftBuffer, y2)
      delete this.btnCanvasLocations.gravityBrakeBtn
      delete this.btnCanvasLocations.oreMineBtn
      delete this.btnCanvasLocations.auxiliaryPowerBtn
    }
    col1YOffset += (sizing.yGap + sizing.yLen)
  }

  private paintDebugData(): void {
    /* Draw Debug info on the top right corner of the screen.
    */
    const cameraMode = this.getCameraMode()

    this.ctx.beginPath()
    this.ctx.font = '16px Arial'
    this.ctx.fillStyle = '#ffffff'
    this.ctx.textAlign = 'right'

    const xOffset = this._camera.gameDisplayCamera.canvasWidth - 15
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

    const {x, y} = this._camera.gameDisplayCamera.getPosition()
    this.ctx.fillText(`camera pos: X: ${x} Y: ${y}`, xOffset, yOffset)
    yOffset += yInterval

    this.ctx.fillText(`camera zoom: ${this._camera.gameDisplayCamera.getZoom()}`, xOffset, yOffset)
    yOffset += yInterval

    this.ctx.fillText(`camera index: ${this._camera.gameDisplayCamera.getZoomIndex()}`, xOffset, yOffset)
    yOffset += yInterval

    this.ctx.fillText(`camera mode: ${cameraMode}`, xOffset, yOffset)
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
    this.ctx.fillText(`ship exploded: ${this._api.frameData.ship.exploded}`, xOffset, yOffset)
    yOffset += yInterval
  }

  private handleBtnClick(btnName: string) {
    console.log({btnName})
    let found = true
    // Menu //
    if(btnName == "engineMenu") {
      this.btnMenuEngineMenu()
    }else if(btnName == "autoPilotMenu") {
      this.btnMenuAutopilotMenu()
    }else if(btnName == "scannerMenuBtn") {
      this.btnMenuScannerMenu()
    }else if(btnName == "EMEBeamMenuBtn") {
      this.btnMenuEMEBeamMenu()
    }else if(btnName == "torpedoMenuBtn") {
      this.btnMenuTorpedoMenu()
    }else if(btnName == "utilitiesMenuBtn") {
      this.btnMenuUtilitiesMenu()
    }// Engine //
    else if(btnName == "engineStartup") {
      this.btnActivateEngine()
    }else if(btnName == "engineShutdown") {
      this.btnDeactivateEngine()
    }else if(btnName == "engineIdle") {
      this.btnUnlightEngine()
    }else if(btnName == "engineIgnite") {
      this.btnLightEngine()
    }else if(btnName == "engineBoost") {
      this.btnBoostEngine()
    }// Autopilot //
    else if(btnName == "autoPilotRetrograde") {
      this.btnAutoPilotHeadingLockRetrograde()
    }else if(btnName == "autoPilotPrograde") {
      this.btnAutoPilotHeadingLockPrograde()
    }else if(btnName == "autoPilotWaypoint") {
      this.btnAutoPilotHeadingLockWaypoint()
    }else if(btnName == "autoPilotTarget") {
      this.btnAutoPilotHeadingLockTarget()
    }else if(btnName == "autoPilotHalt") {
      this.btnAutoPilotHaltPosition()
    }else if(btnName == "autoPilotDisabled") {
      this.btnDisableAutoPilot()
    }// Scanner //
    else if(btnName == "scannerStartBtn") {
      this.btnActivateScanner()
    }else if(btnName == "scannerStopBtn") {
      this.btnDeactivateScanner()
    }else if(btnName == "scannerRadarBtn") {
      this.btnSetScannerModeRadar()
    }else if(btnName == "scannerIRBtn") {
      this.btnSetScannerModeIR()
    }else if(btnName == "scannerUpArrowBtn") {
      this.btnClickScannerCursorUp()
    }else if(btnName == "scannerDownArrowBtn") {
      this.btnClickScannerCursorDown()
    }else if(btnName == "scannerLockBtn") {
      this.btnClickScannerCursorLock()
    }// EME BEAM //
    else if(btnName == "EMEBeamChargeBtn") {
      this.btnClickChargeEBeam()
    }else if(btnName == "EMEBeamPauseBtn") {
      this.btnClickPauseChargeEBeam()
    }else if(btnName == "EMEBeamFireBtn") {
      this.btnClickFireEBeam()
    }// Torpedos //
    else if(btnName == "torpedoMenuSelEMPBtn") {
      this.selectedPneumaticWeapon = EMP_SLUG
    }else if(btnName == "torpedoMenuSelMagnetMineBtn") {
      this.selectedPneumaticWeapon = MAGNET_MINE_SLUG
    }else if(btnName == "torpedoUpArrowBtn") {
      this.btnClickIncreasePneumaticPressure()
    }else if(btnName == "torpedoDownArrowBtn") {
      this.btnClickDecreasePneumaticPressure()
    }else if(btnName == "torpedoFireBtn") {
      this.btnClickFirePneumaticTube()
    }// Utilities //
    else if(btnName == "auxiliaryPowerBtn") {
      this.btnToggleAPU()
    }else if(btnName == "oreMineBtn") {
      this.btnToggleMineOre()
    }else if(btnName == "gravityBrakeBtn") {
      this.btnClickToggleGravBrake()
    }
    else {
      console.warn("unknown btn " + btnName)
      found = false
    }
    if(found) {
      this.clickBtnBoarderAnimationFrame = 1
      this.clickBtnBoarderAnimationButtonName = btnName
    }
  }

  private btnMenuEngineMenu() {
    this.activeBtnGroup = this.activeBtnGroup != ButtonGroup.ENGINE? ButtonGroup.ENGINE: ButtonGroup.NONE
  }

  private btnMenuAutopilotMenu() {
    this.activeBtnGroup = this.activeBtnGroup != ButtonGroup.AUTOPILOT? ButtonGroup.AUTOPILOT: ButtonGroup.NONE
  }

  private btnMenuScannerMenu() {
    this.activeBtnGroup = this.activeBtnGroup != ButtonGroup.SCANNER? ButtonGroup.SCANNER: ButtonGroup.NONE
  }

  private btnMenuEMEBeamMenu() {
    this.activeBtnGroup = this.activeBtnGroup != ButtonGroup.EMEBEAM? ButtonGroup.EMEBEAM: ButtonGroup.NONE
  }

  private btnMenuTorpedoMenu() {
    this.activeBtnGroup = this.activeBtnGroup != ButtonGroup.TORPEDO? ButtonGroup.TORPEDO: ButtonGroup.NONE
  }

  private btnMenuUtilitiesMenu() {
    this.activeBtnGroup = this.activeBtnGroup != ButtonGroup.UTILITIES? ButtonGroup.UTILITIES: ButtonGroup.NONE
  }

  private async btnActivateEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'activate_engine'},
    )
    this._sound.playPrimaryButtonClickSound()
  }

  private async btnDeactivateEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'deactivate_engine'},
    )
    this._sound.playPrimaryButtonClickSound()
  }

  private async btnLightEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'light_engine'},
    )
    this._sound.playPrimaryButtonClickSound()
  }

  private async btnBoostEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'boost_engine'},
    )
    this._sound.playPrimaryButtonClickSound()
  }

  private async btnUnlightEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'unlight_engine'},
    )
    this._sound.playPrimaryButtonClickSound()
  }

  private async btnToggleAPU() {
    if(this._api.frameData.ship.apu_online) {
      this.btnDeactivateAPU()
    } else {
      this.btnActivateAPU()
    }
  }
  private async btnActivateAPU() {
    await this._api.post(
      "/api/rooms/command",
      {command:'activate_apu'},
    )
    this._sound.playUtilityButtonClickSound()
  }

  private async btnDeactivateAPU() {
    await this._api.post(
      "/api/rooms/command",
      {command:'deactivate_apu'},
    )
    this._sound.playUtilityButtonClickSound()
  }

  private async btnSetScannerModeRadar() {
    await this._api.post(
      "/api/rooms/command",
      {command:'set_scanner_mode_radar'},
    )
    this._sound.playPrimaryButtonClickSound()
  }

  private async btnSetScannerModeIR() {
    await this._api.post(
      "/api/rooms/command",
      {command:'set_scanner_mode_ir'},
    )
    this._sound.playPrimaryButtonClickSound()
  }

  private async btnActivateScanner() {
    await this._api.post(
      "/api/rooms/command",
      {command:'activate_scanner'},
    )
    setTimeout(()=>{
      this._pane.scannerPaneVisible = true
    }, 100)
    this._sound.playPrimaryButtonClickSound()
  }

  private async btnDeactivateScanner() {
    this._scanner.scannerTargetIDCursor = null
    await this._api.post(
      "/api/rooms/command",
      {command:'deactivate_scanner'},
    )
    this._pane.scannerPaneVisible = false
    this._sound.playPrimaryButtonClickSound()
  }

  private btnToggleScannerDataWindow() {
    this._pane.scannerPaneVisible = !this._pane.scannerPaneVisible
  }

  // Autopilot button handlers.
  private async btnDisableAutoPilot() {
    await this._api.post(
      "/api/rooms/command",
      {command:'disable_autopilot'},
    )
    this._sound.playPrimaryButtonClickSound()
  }
  private async btnAutoPilotHaltPosition() {
    await this._api.post(
      "/api/rooms/command",
      {command:'run_autopilot', autopilot_program:'position_hold'},
    )
    this._sound.playPrimaryButtonClickSound()
  }
  private async btnAutoPilotHeadingLockTarget() {
    await this._api.post(
      "/api/rooms/command",
      {command:'run_autopilot', autopilot_program:'lock_target'},
    )
    this._sound.playPrimaryButtonClickSound()
  }
  private async btnAutoPilotHeadingLockPrograde() {
    await this._api.post(
      "/api/rooms/command",
      {command:'run_autopilot', autopilot_program:'lock_prograde'},
    )
    this._sound.playPrimaryButtonClickSound()
  }
  private async btnAutoPilotHeadingLockRetrograde() {
    await this._api.post(
      "/api/rooms/command",
      {command:'run_autopilot', autopilot_program:'lock_retrograde'},
    )
    this._sound.playPrimaryButtonClickSound()
  }
  private getWaypointType(uuid: string): string | null {
    for(let i in this._api.frameData.ore_mines) {
      const om = this._api.frameData.ore_mines[i]
      if (om.uuid === uuid) {
        return FEATURE_ORE
      }
    }
    for(let i in this._api.frameData.space_stations) {
      const st = this._api.frameData.space_stations[i]
      if (st.uuid === uuid) {
        return FEATURE_STATION
      }
    }
    console.warn("could not calculate waypoint type")
    return null
  }
  private async btnAutoPilotHeadingLockWaypoint() {
    const wpType = this.getWaypointType(this.wayPointUUID)
    if(!wpType){
      return
    }
    await this._api.post(
      "/api/rooms/command",
      {
        command:'run_autopilot_heading_to_waypoint',
        waypoint_uuid: this.wayPointUUID,
        waypoint_type: wpType,
      },
    )
    this._sound.playPrimaryButtonClickSound()
  }

  private btnClickScannerCursorUp() {
    if(!this._api.frameData.ship || !this._api.frameData.ship.scanner_online) {
      this._scanner.scannerTargetIDCursor = null
      return
    }
    if(!this._api.frameData.ship.scanner_ship_data.length) {
      this._scanner.scannerTargetIDCursor = null
      this._scanner.scannertTargetIndex = null
      return
    }
    if(this._scanner.scannerTargetIDCursor === null) {
      const targetIndex = this._api.frameData.ship.scanner_ship_data.length - 1
      this._scanner.scannerTargetIDCursor = this._api.frameData.ship.scanner_ship_data[targetIndex].id
      this._scanner.scannertTargetIndex = targetIndex
    }
    else {
      const currentIndex = this._api.frameData.ship.scanner_ship_data.map(sc => sc.id).indexOf(this._scanner.scannerTargetIDCursor)
      if(currentIndex === -1) {
        const newIndex = this._api.frameData.ship.scanner_ship_data.length - 1
        this._scanner.scannerTargetIDCursor = this._api.frameData.ship.scanner_ship_data[newIndex].id
        this._scanner.scannertTargetIndex = newIndex
      }
      else {
        const targetIndex = currentIndex === 0 ? this._api.frameData.ship.scanner_ship_data.length - 1 : currentIndex - 1
        this._scanner.scannerTargetIDCursor = this._api.frameData.ship.scanner_ship_data[targetIndex].id
        this._scanner.scannertTargetIndex = targetIndex
      }
    }
    this._sound.playPrimaryButtonClickSound()
  }

  private btnClickScannerCursorDown() {
    if(!this._api.frameData.ship || !this._api.frameData.ship.scanner_online) {
      this._scanner.scannerTargetIDCursor = null
      return
    }
    if(!this._api.frameData.ship.scanner_ship_data.length) {
      this._scanner.scannerTargetIDCursor = null
      this._scanner.scannertTargetIndex = null
      return
    }
    if(this._scanner.scannerTargetIDCursor === null) {
      this._scanner.scannerTargetIDCursor = this._api.frameData.ship.scanner_ship_data[0].id
      this._scanner.scannertTargetIndex = 0
    }
    else {
      const currentIndex = this._api.frameData.ship.scanner_ship_data.map(sc => sc.id).indexOf(this._scanner.scannerTargetIDCursor)
      if(currentIndex === -1) {
        this._scanner.scannerTargetIDCursor = this._api.frameData.ship.scanner_ship_data[0].id
        this._scanner.scannertTargetIndex = 0
      }
      else {
        const targetIndex = currentIndex === this._api.frameData.ship.scanner_ship_data.length - 1 ? 0 : currentIndex + 1
        this._scanner.scannerTargetIDCursor = this._api.frameData.ship.scanner_ship_data[targetIndex].id
        this._scanner.scannertTargetIndex = targetIndex
      }
    }
    this._sound.playPrimaryButtonClickSound()
  }

  private async btnClickScannerCursorLock () {
    if(!this._api.frameData.ship || !this._api.frameData.ship.scanner_online) {
      this._scanner.scannerTargetIDCursor = null
      return
    }
    const targetIndex = this._api.frameData.ship.scanner_ship_data.map(sc => sc.id).indexOf(this._scanner.scannerTargetIDCursor)
    if(targetIndex === -1) {
      this._scanner.scannerTargetIDCursor = null
      return
    }
    if(this._scanner.scannerTargetIDCursor === null) {
      return
    }
    if(this._api.frameData.ship.scanner_locking) {
      return
    }
    if(this._api.frameData.ship.scanner_locked && this._scanner.scannerTargetIDCursor === this._api.frameData.ship.scanner_lock_target) {
      return
    }
    await this._api.post(
      "/api/rooms/command",
      {command: 'set_scanner_lock_target', target: this._scanner.scannerTargetIDCursor},
    )
    this._sound.playPrimaryButtonClickSound()
  }

  private async btnClickChargeEBeam() {
    if(!this._api.frameData.ship.ebeam_charging && !this._api.frameData.ship.ebeam_firing) {
      await this._api.post(
        "/api/rooms/command",
        {command:'charge_ebeam'},
      )
    }
    this._sound.playPrimaryButtonClickSound()
  }

  private async btnClickPauseChargeEBeam() {
    if(this._api.frameData.ship.ebeam_charging) {
      await this._api.post(
        "/api/rooms/command",
        {command:'pause_charge_ebeam'},
      )
      this._sound.playPrimaryButtonClickSound()
    }
  }

  private async btnClickFireEBeam() {
    if(this._api.frameData.ship.ebeam_can_fire) {
      await this._api.post(
        "/api/rooms/command",
        {command:'fire_ebeam'},
      )
      this._sound.playPrimaryButtonClickSound()
    }
  }

  private btnClickFirePneumaticTube() {
    if(this.selectedPneumaticWeapon == MAGNET_MINE_SLUG) {
      this._api.post(
        "/api/rooms/command",
        {command:'launch_magnet_mine', launch_velocity: this.lauchVelocity},
      )
    } else if (this.selectedPneumaticWeapon == EMP_SLUG) {
      this._api.post(
        "/api/rooms/command",
        {command:'launch_emp', launch_velocity: this.lauchVelocity},
      )
    } else {
      console.warn("unknown selected pneumatic weapon " + this.selectedPneumaticWeapon)
    }
  }

  private btnClickIncreasePneumaticPressure() {
    this.lauchVelocity = Math.min(
      this.maxLaunchVelocity,
      this.lauchVelocity + this.launchVelocityInterval
    )
    console.log(this.lauchVelocity)
  }
  private btnClickDecreasePneumaticPressure() {
    this.lauchVelocity = Math.max(
      this.minLaunchVelocity,
      this.lauchVelocity - this.launchVelocityInterval
    )
    console.log(this.lauchVelocity)
  }

  private async btnClickToggleGravBrake() {
    console.log("btnClickToggleGravBrake()")
    if (this._api.frameData.ship.gravity_brake_deployed) {
      this._api.post(
        "/api/rooms/command",
        {command:'retract_gravity_brake'},
      )
      this._sound.playUtilityButtonClickSound()
      return
    }
    else if (
      this._api.frameData.ship.gravity_brake_position == 0
    ) {
      this._api.post(
        "/api/rooms/command",
        {command:'extend_gravity_brake'},
      )
      this._sound.playUtilityButtonClickSound()
      return
    }
  }

  private async btnToggleMineOre() {
    if(!this._api.frameData.ship.parked_at_ore_mine === null) {
      console.warn("btn disabled")
      return
    }
    if(!this._api.frameData.ship.mining_ore) {
      this._api.post(
        "/api/rooms/command",
        {command:'start_ore_mining'},
      )
      this._sound.playUtilityButtonClickSound()
      return
    } else {
      this._api.post(
        "/api/rooms/command",
        {command:'stop_ore_mining'},
      )
      this._sound.playUtilityButtonClickSound()
      return
    }
  }

  private async btnToggleAllChatPane(){
    this._pane.toggleAllChatPane()
  }

  private btnToggleMainMenuPane() {
    this._pane.toggleMainMenuPane()
  }

  private async btnToggleShipPane(){
    this._pane.toggleShipPane()
  }

}
