
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

const CAMERA_MODE_SHIP = "ship"
const CAMERA_MODE_VISION = "vision"
const CAMERA_MODE_MAP = "map"

@Component({
  selector: 'app-gamedisplay',
  templateUrl: './gamedisplay.component.html',
  styleUrls: ['./gamedisplay.component.css']
})
export class GamedisplayComponent implements OnInit {


  @ViewChild("graphicsCanvas") canvas: ElementRef
  @ViewChild("graphicsCanvasContainer") canvasContainer: ElementRef
  @ViewChild("sidebarElement") sidebarElement: ElementRef

  public lauchVelocity: number = 65;


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
  private clickAnimationFrame: number | null = null
  private clickAnimationCanvasX: number | null = null
  private clickAnimationCanvasY: number | null = null

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
  public mineBtnTxtColor = "#000000"

  public wayPoint: PointCoord | null = null
  public wayPointUUID: string | null = null

  public selectedPneumaticWeapon = MAGNET_MINE_SLUG
  private allPneumaticWeapons = [
    MAGNET_MINE_SLUG,
    EMP_SLUG,
  ]

  constructor(
    public _api: ApiService,
    private _sound: SoundService,
    public _camera: CameraService,
    private _formatting: FormattingService,
    public _pane: PaneService,
    public _allchat: AllchatService,
    private _draw: DrawingService,
    public _scanner: ScannerService,
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

  setCameraModeVision() {
    if(this.cameraMode === CAMERA_MODE_SHIP) {
      this.previousCameraZoomIndex = this._camera.gameDisplayCamera.getZoomIndex()
    }
    this.cameraMode = CAMERA_MODE_VISION
    this.setZoomForCameraModeVision()
  }

  setZoomForCameraModeVision() {
    const visionRadius = this._api.frameData.ship.visual_range
    const canvasRadius = Math.min(
      this._camera.gameDisplayCamera.canvasHalfHeight,
      this._camera.gameDisplayCamera.canvasHalfWidth,
    )
    this._camera.gameDisplayCamera.setZoom(
      Math.ceil(visionRadius / canvasRadius * this._api.frameData.map_config.units_per_meter)
    )
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
    else if (this.previousCameraMode == CAMERA_MODE_VISION) {
      this.setCameraModeVision()
    }
    else {
      console.warn("could not select a camera profile after closing map.")
    }
  }

  @HostListener('window:resize', ['$event'])
  private handleWindowResize():void {
    location.reload() // TODO: This is shit. Need a better solution.
  }

  @HostListener('document:keypress', ['$event'])
  private handleKeyboardEvent(event: KeyboardEvent) {
    if(this._pane.getInputIsFocused()) {
      return
    }
    const key = event.key.toLocaleLowerCase()
    console.log({gameKeystroke: key})
    if (key === 'm') {
      this.toggleMap()
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

  public handleMouseClickInCanvas(event: any): void {
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
      if(!this._api.frameData.ship.autopilot_program && cameraMode !== CAMERA_MODE_MAP) {
        this.clickAnimationFrame = 1
        this.clickAnimationCanvasX = mouseCanvasX
        this.clickAnimationCanvasY = mouseCanvasY
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

  private setupCanvasContext(): void {
    this.ctx = this.ctx || this.canvas.nativeElement.getContext("2d")
  }

  private resizeCanvas() {
    setTimeout(() => {
      console.log("resizeCanvas()")
      this.canvas.nativeElement.width = this.canvas.nativeElement.offsetWidth
      this.canvas.nativeElement.height = this.canvas.nativeElement.offsetHeight
      this._camera.gameDisplayCamera.setCanvasWidthHeight(
        this.canvas.nativeElement.offsetWidth,
        this.canvas.nativeElement.offsetHeight,
      )
    })
  }

  private setCanvasColor(): void {
    this.canvas.nativeElement.style.backgroundColor = "#000000" // Black
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

  private paintDisplay(): void {

    if (this._api.frameData === null) {
      window.requestAnimationFrame(this.paintDisplay.bind(this))
      return
    }

    if(this._api.frameData.ship.gravity_brake_extending || this._api.frameData.ship.gravity_brake_retracting) {
      this.gravBrakeBtnBkColor = "#b2b500"
      this.grabBrakeBtnTxtColor = "#b50000"
    } else if (this._api.frameData.ship.gravity_brake_deployed) {
      this.gravBrakeBtnBkColor = "#00b51b"
      this.grabBrakeBtnTxtColor = "#ffffff"
    } else if (this._api.frameData.ship.gravity_brake_position == 0) {
      this.gravBrakeBtnBkColor = "#b50000"
      this.grabBrakeBtnTxtColor = "#ffffff"
    }

    if(this._api.frameData.ship.apu_starting) {
      this.apuBtnBkColor = "#b2b500"
      this.apuBtnTxtColor = "#b50000"
    }
    else if (this._api.frameData.ship.apu_online) {
      this.apuBtnBkColor = "#00b51b"
      this.apuBtnTxtColor = "#ffffff"
    } else {
      this.apuBtnBkColor = "#b50000"
      this.apuBtnTxtColor = "#ffffff"
    }

    if(this._api.frameData.ship.mining_ore) {
      this.mineBtnBkColor = "#00b51b"
      this.mineBtnTxtColor = "#ffffff"
    }
    else {
      this.mineBtnBkColor = "#b50000"
      this.mineBtnTxtColor = "#ffffff"
    }

    const camCoords = this._camera.gameDisplayCamera.getPosition()
    const cameraMode = this.getCameraMode()
    if(camCoords.x === null || camCoords.y === null) {
      this._camera.gameDisplayCamera.setPosition(
        this._api.frameData.ship.coord_x,
        this._api.frameData.ship.coord_y,
      )
    }

    this.clearCanvas()

    if (cameraMode === CAMERA_MODE_SHIP || cameraMode === CAMERA_MODE_VISION) {
      this._camera.gameDisplayCamera.setPosition(
        this._api.frameData.ship.coord_x,
        this._api.frameData.ship.coord_y,
      )
      if(cameraMode === CAMERA_MODE_VISION && this._api.frameData.game_frame % 60 == 0) {
        this.setZoomForCameraModeVision()
      }
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

    // Corner overlays
    const tubeWeaponCt = this.getCurrentTubeWeaponCount()
    this._draw.drawBottomLeftOverlay(
      this.ctx,
      this._camera.gameDisplayCamera,
      cameraMode === CAMERA_MODE_MAP,
      `TUBE: ${tubeWeaponCt > 0 ? tubeWeaponCt : "EMPTY"} ${this.getHumanReadableCurrentTubeWeapon()}`
    )
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
    if(this.clickAnimationFrame) {
      this.ctx.beginPath()
      this.ctx.strokeStyle = "#00ff00"
      this.ctx.lineWidth = 3
      this.ctx.arc(
        this.clickAnimationCanvasX,
        this.clickAnimationCanvasY,
        this.clickAnimationFrame * 2.5,
        0,
        TWO_PI,
      )
      this.ctx.stroke()
      this.clickAnimationFrame++
      if (this.clickAnimationFrame > 10) {
        this.clickAnimationFrame = null
      }
    }

    if(this.isDebug) {
      this.paintDebugData();
    }
    this._sound.runSoundFXEngine();
    window.requestAnimationFrame(this.paintDisplay.bind(this))
  }

  private clearCanvas(): void {
    this.ctx.beginPath()
    this.ctx.clearRect(0, 0, this._camera.gameDisplayCamera.canvasWidth * 2, this._camera.gameDisplayCamera.canvasHeight * 2) // *2 because of bug where corner is not cleared
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

  public async btnActivateEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'activate_engine'},
    )
    this._sound.playPrimaryButtonClickSound()
  }

  public async btnDeactivateEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'deactivate_engine'},
    )
    this._sound.playPrimaryButtonClickSound()
  }

  public async btnLightEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'light_engine'},
    )
    this._sound.playPrimaryButtonClickSound()
  }

  public async btnBoostEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'boost_engine'},
    )
    this._sound.playPrimaryButtonClickSound()
  }

  public async btnUnlightEngine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'unlight_engine'},
    )
    this._sound.playPrimaryButtonClickSound()
  }

  public async btnToggleAPU() {
    if(this._api.frameData.ship.apu_online) {
      this.btnDeactivateAPU()
    } else {
      this.btnActivateAPU()
    }
  }
  public async btnActivateAPU() {
    await this._api.post(
      "/api/rooms/command",
      {command:'activate_apu'},
    )
    this._sound.playUtilityButtonClickSound()
  }

  public async btnDeactivateAPU() {
    await this._api.post(
      "/api/rooms/command",
      {command:'deactivate_apu'},
    )
    this._sound.playUtilityButtonClickSound()
  }

  public async btnSetScannerModeRadar() {
    await this._api.post(
      "/api/rooms/command",
      {command:'set_scanner_mode_radar'},
    )
    this._sound.playPrimaryButtonClickSound()
  }

  public async btnSetScannerModeIR() {
    await this._api.post(
      "/api/rooms/command",
      {command:'set_scanner_mode_ir'},
    )
    this._sound.playPrimaryButtonClickSound()
  }

  public async btnActivateScanner() {
    await this._api.post(
      "/api/rooms/command",
      {command:'activate_scanner'},
    )
    setTimeout(()=>{
      this._pane.scannerPaneVisible = true
    }, 100)
    this._sound.playPrimaryButtonClickSound()
  }

  public async btnDeactivateScanner() {
    this._scanner.scannerTargetIDCursor = null
    await this._api.post(
      "/api/rooms/command",
      {command:'deactivate_scanner'},
    )
    this._pane.scannerPaneVisible = false
    this._sound.playPrimaryButtonClickSound()
  }

  btnToggleScannerDataWindow() {
    this._pane.scannerPaneVisible = !this._pane.scannerPaneVisible
  }

  // Autopilot button handlers.
  public async btnDisableAutoPilot() {
    await this._api.post(
      "/api/rooms/command",
      {command:'disable_autopilot'},
    )
    this._sound.playPrimaryButtonClickSound()
  }
  public async btnAutoPilotHaltPosition() {
    await this._api.post(
      "/api/rooms/command",
      {command:'run_autopilot', autopilot_program:'position_hold'},
    )
    this._sound.playPrimaryButtonClickSound()
  }
  public async btnAutoPilotHeadingLockTarget() {
    await this._api.post(
      "/api/rooms/command",
      {command:'run_autopilot', autopilot_program:'lock_target'},
    )
    this._sound.playPrimaryButtonClickSound()
  }
  public async btnAutoPilotHeadingLockPrograde() {
    await this._api.post(
      "/api/rooms/command",
      {command:'run_autopilot', autopilot_program:'lock_prograde'},
    )
    this._sound.playPrimaryButtonClickSound()
  }
  public async btnAutoPilotHeadingLockRetrograde() {
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
  public async btnAutoPilotHeadingLockWaypoint() {
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

  btnClickScannerCursorUp() {
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

  btnClickScannerCursorDown() {
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

  async btnClickScannerCursorLock () {
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

  async btnClickChargeEBeam() {
    if(!this._api.frameData.ship.ebeam_charging && !this._api.frameData.ship.ebeam_firing) {
      await this._api.post(
        "/api/rooms/command",
        {command:'charge_ebeam'},
      )
    }
    this._sound.playPrimaryButtonClickSound()
  }

  async btnClickPauseChargeEBeam() {
    if(this._api.frameData.ship.ebeam_charging) {
      await this._api.post(
        "/api/rooms/command",
        {command:'pause_charge_ebeam'},
      )
      this._sound.playPrimaryButtonClickSound()
    }
  }

  async btnClickFireEBeam() {
    if(this._api.frameData.ship.ebeam_can_fire) {
      await this._api.post(
        "/api/rooms/command",
        {command:'fire_ebeam'},
      )
      this._sound.playPrimaryButtonClickSound()
    }
  }

  btnClickCyclePneumaticTube() {
    const totalCount = this.allPneumaticWeapons.length
    const currentIndex = this.allPneumaticWeapons.indexOf(this.selectedPneumaticWeapon)
    if(currentIndex == (totalCount - 1)) {
      this.selectedPneumaticWeapon = this.allPneumaticWeapons[0]
    } else {
      this.selectedPneumaticWeapon = this.allPneumaticWeapons[currentIndex + 1]
    }
    console.log("selected " + this.selectedPneumaticWeapon)
  }

  btnClickFirePneumaticTube() {
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

  async btnClickToggleGravBrake() {
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

  async btnToggleMineOre() {
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
