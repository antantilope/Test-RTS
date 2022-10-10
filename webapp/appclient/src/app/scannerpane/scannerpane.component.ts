import { Component, OnInit, ElementRef, ViewChild } from '@angular/core';
import { Subscription } from 'rxjs'

import { CameraService } from '../camera.service';
import { PaneService } from '../pane.service';

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

  constructor(
    public _pane: PaneService,
    private _camera: CameraService,
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
    this.select()
    this.resizeCanvas()
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
      const height = this.paneElement.nativeElement.height - this.titleBar.nativeElement.height
      this.canvas.nativeElement.width = this.canvas.nativeElement.offsetWidth
      this.canvas.nativeElement.offsetHeight = height
      this.canvas.nativeElement.height = height
      this._camera.scannerPaneCamera.setCanvasWidthHeight(
        this.canvas.nativeElement.offsetWidth,
        this.canvas.nativeElement.offsetHeight,
      )
    })
  }

}
