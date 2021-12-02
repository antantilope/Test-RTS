
import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';

import { ApiService } from '../api.service';
import { ScannerDataElement } from '../models/drawable-objects.model';
import { PaneService } from '../pane.service';


@Component({
  selector: 'app-scannerpane',
  templateUrl: './scannerpane.component.html',
  styleUrls: ['./scannerpane.component.css']
})
export class ScannerpaneComponent implements OnInit {

  @ViewChild("paneElem") paneElem: ElementRef;

  public selectionCursor: string | null = null


  constructor(
    public _pane: PaneService,
    public _api: ApiService,
  ) { }

  ngOnInit(): void {
  }

  ngAfterViewInit() {
    console.log("ScannerpaneComponent::ngAfterViewInit")
    this.registerMouseEventListener()
  }

  private registerMouseEventListener():void {
    this.paneElem.nativeElement.addEventListener('mouseenter', ()=>{
      this._pane.mouseInPane = true
    })
    this.paneElem.nativeElement.addEventListener('mouseleave', ()=>{
      this._pane.mouseInPane = false
    })
  }


  lockSelectUpClick() {
    if (!this._api.frameData.ship.scanner_data.length) {
      this.selectionCursor = null
      return
    }
    const lastIx = this._api.frameData.ship.scanner_data.length - 1
    if(this.selectionCursor === null) {
      this.selectionCursor = this._api.frameData.ship.scanner_data[lastIx].id
      return
    }
    const currTargIndex = this._api.frameData.ship.scanner_data.map(se => se.id).indexOf(this.selectionCursor)
    if(currTargIndex === -1) {
      this.selectionCursor = this._api.frameData.ship.scanner_data[0].id
      return
    }
    const targetIndex = currTargIndex > 0 ? currTargIndex - 1 : lastIx
    this.selectionCursor = this._api.frameData.ship.scanner_data[targetIndex].id
  }

  lockSelectDownClick() {
    if (!this._api.frameData.ship.scanner_data.length) {
      this.selectionCursor = null
      return
    }
    if(this.selectionCursor === null) {
      this.selectionCursor = this._api.frameData.ship.scanner_data[0].id
      return
    }
    const lastIx = this._api.frameData.ship.scanner_data.length - 1
    const currTargIndex = this._api.frameData.ship.scanner_data.map(se => se.id).indexOf(this.selectionCursor)
    if(currTargIndex === -1) {
      this.selectionCursor = this._api.frameData.ship.scanner_data[lastIx].id
      return
    }
    const targetIndex = currTargIndex < lastIx ? currTargIndex + 1 : 0
    this.selectionCursor = this._api.frameData.ship.scanner_data[targetIndex].id
  }

  async lockSelectClick() {
    if(this.selectionCursor === null) {
      return
    }
    const currTargIndex = this._api.frameData.ship.scanner_data.map(se => se.id).indexOf(this.selectionCursor)
    if(currTargIndex === -1) {
      return
    }
    await this._api.post(
      "/api/rooms/command",
      {command: 'set_scanner_lock_target', target: this.selectionCursor},
    )
  }

  lockClearSelectClick() {
    this.selectionCursor = null
  }

}
