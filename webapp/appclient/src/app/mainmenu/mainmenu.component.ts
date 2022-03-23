import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { PaneService } from '../pane.service';
import { Subscription } from 'rxjs'
import { ApiService } from '../api.service';


@Component({
  selector: 'app-mainmenu',
  templateUrl: './mainmenu.component.html',
  styleUrls: ['./mainmenu.component.css']
})
export class MainmenuComponent implements OnInit {

  private paneName: string;
  public exitBtnText = "Leave Game"
  public waitingToExit = false

  @ViewChild("paneElement") paneElement: ElementRef
  zIndexesUpdatedSubscription: Subscription

  constructor(
    public _pane: PaneService,
    private _api: ApiService,
  ) {
    this.paneName = this._pane.PANE_MAIN_MENU
  }

  ngOnInit(): void {
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
    this.paneElement.nativeElement.addEventListener('mouseenter', ()=>{
      this._pane.registerMouseEnteringPane(this.paneName)
    })
    this.paneElement.nativeElement.addEventListener('mouseleave', ()=>{
      this._pane.registerMouseLeavingPane(this.paneName)
    })
    this.select()
  }

  select() {
    this._pane.addToTopOfZIndexes(this.paneName)
  }

  async btnClickLeaveMatch() {
    if(this.waitingToExit) {
      return
    }
    this.waitingToExit = true
    const resp = await this._api.post(
      "/api/rooms/command",
      {command:'leave_game'},
    )
    setTimeout(()=>{
      location.reload()
    }, 1000)
  }

}
