
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

  public getTargets(): ScannerDataElement[] {
    return Object.values(this._api.frameData.ship.scanner_data)
  }

}
