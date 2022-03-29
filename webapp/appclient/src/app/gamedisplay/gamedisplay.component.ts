
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
import {
  CameraService,
  CAMERA_MODE_SHIP,
  CAMERA_MODE_SCANNER,
  CAMERA_MODE_FREE,
  CAMERA_MODE_MAP,
} from '../camera.service'
import { FormattingService } from '../formatting.service'
import { AllchatService } from "../allchat.service"
import { PointCoord } from '../models/point-coord.model'
import { DrawingService } from '../drawing.service'
import { TWO_PI } from '../constants'

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


  private ctx: CanvasRenderingContext2D | null = null

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

  private wayPoint: PointCoord | null = null
  private wayPointUUID: string | null = null

  constructor(
    public _api: ApiService,
    public _camera: CameraService,
    private _formatting: FormattingService,
    public _pane: PaneService,
    public _allchat: AllchatService,
    private _draw: DrawingService,
  ) {
    console.log("GamedisplayComponent::constructor")
  }

  ngOnInit(): void {
    console.log("GamedisplayComponent::ngOnInit")
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

  }

  ngOnDestroy() {
    console.log("GamedisplayComponent::ngOnDestroy")
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
      this._camera.toggleMap()
    } else if (key === 'n') {
      this._camera.cycleMode()
    }
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

    this.canvas.nativeElement.addEventListener('mouseover', () => {
      this.mouseInCanvas = true
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
      } else {
        console.log("no click")
        console.log({
          "!this.mouseMovedWhileDown": !this.mouseMovedWhileDown,
          "this.mouseInCanvas": this.mouseInCanvas,
          "!this._pane.mouseInPane()": !this._pane.mouseInPane(),
        })
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
      !this._api.frameData.ship.autopilot_program
      && this.drawableObjects !== null
      && typeof this.drawableObjects.ships[0] !== 'undefined'
      && this.drawableObjects.ships[0].isSelf
    ) {
      const mode = this._camera.getMode()
      if(mode == CAMERA_MODE_SHIP || mode == CAMERA_MODE_SCANNER) {
        this.clickAnimationFrame = 1
        this.clickAnimationCanvasX = mouseCanvasX
        this.clickAnimationCanvasY = mouseCanvasY
        this.handleMouseClickInCanvasHeadingAdjust(mouseCanvasX, mouseCanvasY)
      }
      else if (mode == CAMERA_MODE_MAP) {
        this.handleMouseClickInCanvasDropWaypoint(mode, mouseCanvasX, mouseCanvasY)
      }

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
    const cameraPosition = this._camera.getPosition()
    for(let i in this._api.frameData.ore_mines) {
      let om = this._api.frameData.ore_mines[i]
      let omCanvasCoord = this._camera.mapCoordToCanvasCoord(
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
      let stCanvasCoord = this._camera.mapCoordToCanvasCoord(
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

    const camCoords = this._camera.getPosition()
    const camMode = this._camera.getMode()
    if(camCoords.x === null || camCoords.y === null) {
      this._camera.setPosition(
        this._api.frameData.ship.coord_x,
        this._api.frameData.ship.coord_y,
      )
    }

    this.clearCanvas()

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
    this._draw.drawVisionCircles(this.ctx, drawableObjects.visionCircles)

    // Draw Map boundary
    this._draw.drawMapBoundary(this.ctx, drawableObjects.mapWall);

    // Add map features
    this._draw.drawSpaceStations(this.ctx)
    this._draw.drawMiningLocations(this.ctx)

    // Waypoint, if one is set
    if(this.wayPoint !== null) {
      this._draw.drawWaypoint(this.ctx, this.wayPoint)
    }

    // expect smallest vision circle at end of array
    const lastIx = drawableObjects.visionCircles.length - 1
    if(lastIx > -1) {
      this._draw.drawVelocityAndHeadingLine(
        this.ctx,
        drawableObjects.visionCircles[lastIx],
      )
    }

    // Ships
    for(let i in drawableObjects.ships) {
      const drawableShip: DrawableShip = drawableObjects.ships[i]
      this._draw.drawShip(
        this.ctx,
        drawableObjects.ships[i],
        this.scannerTargetIDCursor,
      )
    }

    // E-Beams
    this._draw.drawEbeams(this.ctx, drawableObjects.ebeamRays)

    // Corner overlays
    this._draw.drawBottomLeftOverlay(this.ctx)
    this._draw.drawTopLeftOverlay(this.ctx);
    this._draw.drawBottomRightOverlay(this.ctx)
    if(!this.isDebug && this._api.frameData.ship.alive) {
      this._draw.drawTopRightOverlay(this.ctx)
    }

    // Front center and alerts
    this._draw.drawFrontAndCenterAlerts(this.ctx)

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

    this.ctx.fillText(`camera index: ${this._camera.getZoomIndex()}`, xOffset, yOffset)
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

    this.ctx.fillText(`camera mode: ${this._camera.getMode()}`, xOffset, yOffset)
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

  async btnClickToggleGravBrake() {
    console.log("btnClickToggleGravBrake()")
    if (this._api.frameData.ship.gravity_brake_deployed) {
      return this._api.post(
        "/api/rooms/command",
        {command:'retract_gravity_brake'},
      )
    }
    else if (
      this._api.frameData.ship.gravity_brake_position == 0
    ) {
      return this._api.post(
        "/api/rooms/command",
        {command:'extend_gravity_brake'},
      )
    } else {
      console.log("gravbrake doing nothing")
    }
  }

  async btnToggleMineOre() {
    if(!this._api.frameData.ship.parked_at_ore_mine === null) {
      console.warn("btn disabled")
      return
    }
    if(!this._api.frameData.ship.mining_ore) {
      return this._api.post(
        "/api/rooms/command",
        {command:'start_ore_mining'},
      )
    } else {
      return this._api.post(
        "/api/rooms/command",
        {command:'stop_ore_mining'},
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
