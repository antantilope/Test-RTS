import { Component, OnInit, ElementRef, ViewChild } from '@angular/core';
import { Subscription } from 'rxjs'
import { ApiService } from '../api.service';


import { CameraService } from '../camera.service';
import { PaneService } from '../pane.service';
import { TIMER_SLUG_SCANNER_STARTUP } from "../constants"
import { TimerItem } from "../models/timer-item.model"

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

  constructor(
    public _pane: PaneService,
    private _camera: CameraService,
    private _api: ApiService,
  ) { }

  ngOnInit(): void {
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
    this.setCanvasColor()
    setTimeout(()=>{
      this.paintDisplay()
    })
  }

  private setupCanvasContext(): void {
    this.ctx = this.ctx || this.canvas.nativeElement.getContext("2d")
    console.log(this.ctx)
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
      console.log({calculatedHeight: height})
      this.canvas.nativeElement.width = this.canvas.nativeElement.offsetWidth
      this.canvas.nativeElement.height = height// this.canvas.nativeElement.offsetHeight
      this._camera.scannerPaneCamera.setCanvasWidthHeight(
        this.canvas.nativeElement.offsetWidth,
        this.canvas.nativeElement.offsetHeight,
      )
    })
  }

  private setCanvasColor(): void {
    this.canvas.nativeElement.style.backgroundColor = "#001800" // Dark Green
  }

  private clearCanvas(): void {
    this.ctx.beginPath()
    this.ctx.clearRect(
      0, 0,
      this._camera.scannerPaneCamera.canvasWidth * 2,  // *2 because of bug where corner is not cleared
      this._camera.scannerPaneCamera.canvasHeight * 2, //
    )
  }

  paintDisplay(): void {
    // console.log("paintDisplay()")
    const ship = this._api.frameData.ship
    this.clearCanvas()

    if(!ship.scanner_online) {
      this.drawScannerUnavailableMessage()
      window.requestAnimationFrame(this.paintDisplay.bind(this))
      return
    }
    this.drawTopRightOverlay()

    window.requestAnimationFrame(this.paintDisplay.bind(this))
  }

  private drawScannerUnavailableMessage() {
    const isStarting = this._api.frameData.ship.scanner_starting
    this.ctx.beginPath()
    this.ctx.font = 'bold 40px Courier New'
    this.ctx.fillStyle = '#ffffff'
    this.ctx.textAlign = 'center'
    this.ctx.textBaseline = "bottom"
    this.ctx.fillText(
      isStarting ? "LOADING" : "OFFLINE",
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

  private drawTopRightOverlay() {
    let mode;
    if(this._api.frameData.ship.scanner_mode == "radar") {
      mode = "RADAR"
    } else if(this._api.frameData.ship.scanner_mode == "ir") {
      mode = "THERMAL"
    } else { throw new Error(`unknown scanner mode ${this._api.frameData.ship.scanner_mode}`)}
    let yOffset = 5;
    const xOffset = this._camera.scannerPaneCamera.canvasWidth - 5
    const yTextInterval = 30
    this.ctx.beginPath()
    this.ctx.font = '20px Courier New'
    this.ctx.fillStyle = '#ffffff'
    this.ctx.textAlign = 'right'
    this.ctx.textBaseline = "top"
    this.ctx.fillText(
      mode, xOffset, yOffset
    )
  }

}
