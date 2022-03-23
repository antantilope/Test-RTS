import { Component, OnInit, ViewChild, ElementRef } from '@angular/core'
import { Subscription } from 'rxjs'

import { AllchatService } from "../allchat.service"
import { ApiService } from '../api.service'
import { PaneService } from '../pane.service'

@Component({
  selector: 'app-allchat',
  templateUrl: './allchat.component.html',
  styleUrls: ['./allchat.component.css']
})
export class AllchatComponent implements OnInit {

  private paneName: string

  @ViewChild("paneElement") paneElement: ElementRef
  @ViewChild("paneBodyElement") paneBodyElement: ElementRef
  @ViewChild("textInputElement") textInputElement: ElementRef

  msgInput:string = "";
  newAllchatAddedSubscription: Subscription
  zIndexesUpdatedSubscription: Subscription

  constructor(
    public _allchat: AllchatService,
    public _api: ApiService,
    public _pane: PaneService,
  ) {
    console.log("allchat componenent::constructor()")
    this._allchat.resetUnreadCount()
    this.paneName = this._pane.PANE_ALL_CHAT
  }

  ngOnInit(): void {
    console.log("allchat componenent::ngOnInit()")
    this.newAllchatAddedSubscription = this._allchat.newAllchatAdded.subscribe(()=>{
      setTimeout(()=>{
        this.scrollPaneToBottom()
      }, 25);
    })
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

  ngOnDestroy()	{
    this.newAllchatAddedSubscription.unsubscribe();
    this.zIndexesUpdatedSubscription.unsubscribe();
  }


  public async enterKeyDown(event) {
    const msg = this.msgInput.trim()
    if(msg.length) {
      this._api.sendPublicMessage(msg)
      this.msgInput = ""
    }
  }

  public scrollPaneToBottom() {
    this.paneBodyElement.nativeElement.scrollTop = this.paneBodyElement.nativeElement.scrollHeight;
  }

  focusOnInput() {
    setTimeout(()=>{
      console.log("focusOnInput()");
      this.textInputElement.nativeElement.focus();
    });
  }

  select () {
    this.focusOnInput()
    this._pane.addToTopOfZIndexes(this.paneName)
  }

}
