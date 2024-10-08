import { Subscription } from 'rxjs'
import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';

import { PaneService } from '../pane.service';
import { ApiService } from '../api.service';



@Component({
  selector: 'app-shippane',
  templateUrl: './shippane.component.html',
  styleUrls: ['./shippane.component.css']
})
export class ShippaneComponent implements OnInit {

  public paneName: string;
  @ViewChild("paneElement") paneElement: ElementRef
  @ViewChild("paneBodyElement") paneBodyElement: ElementRef
  zIndexesUpdatedSubscription: Subscription

  public selectedSubPane: string
  public subPaneNameEngineering = "engineering"
  public subPaneNameUpgrades = "upgrades"
  public subPaneNameStation = "station"

  constructor(
    public _pane: PaneService,
    public _api: ApiService,
  ) {
    this.paneName = this._pane.PANE_SHIP
  }

  ngOnInit(): void {
    console.log("shippane componenent::ngOnInit()")
    this.select()
    // this.selectEngineeringSubPane()
    this.zIndexesUpdatedSubscription = this._pane.zIndexesUpdated.subscribe((zIndexes: string[]) => {
      const paneZIndex = zIndexes.indexOf(this.paneName);
      if(paneZIndex === -1) {
        return console.error(
          "cannot find paneName " + this.paneName + " in zIndexes " + JSON.stringify(zIndexes))
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

  ngAfterViewInit() {
    // FIXME: this setTimeout seems super jank but cleans up errors.
    setTimeout(() =>{
      this.paneElement.nativeElement.addEventListener('mouseenter', ()=>{
        this._pane.registerMouseEnteringPane(this.paneName)
      })
      this.paneElement.nativeElement.addEventListener('mouseleave', ()=>{
        this._pane.registerMouseLeavingPane(this.paneName)
      })
      this.select()
      if(this._pane.lastShipPaneSubPane) {
        this.selectedSubPane = this._pane.lastShipPaneSubPane
      } else {
        this.selectEngineeringSubPane()
      }
    })
  }

  ngOnDestroy()	{
    this.zIndexesUpdatedSubscription.unsubscribe();
  }


  select () {
    this._pane.addToTopOfZIndexes(this.paneName)
  }

  selectEngineeringSubPane() {
    this.selectedSubPane = this.subPaneNameEngineering
    this._pane.lastShipPaneSubPane = this.subPaneNameEngineering // Remeber pane so ship pane reopens to same pane.
  }

  selectUpgradesSubPane() {
    this.selectedSubPane = this.subPaneNameUpgrades
    this._pane.lastShipPaneSubPane = this.subPaneNameUpgrades // Remeber pane so ship pane reopens to same pane.
  }

  selectStationSubPane() {
      if(this._api.frameData.ship.docked_at_station !== null) {
        this.selectedSubPane = this.subPaneNameStation
        this._pane.lastShipPaneSubPane = this.subPaneNameStation // Remeber pane so ship pane reopens to same pane.
      } else {
        console.warn("could not open station sub pane")
        this.selectEngineeringSubPane()
      }
  }


}
