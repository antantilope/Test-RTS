import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { Subscription } from 'rxjs'

import { AllchatService } from "../allchat.service"
import { ApiService } from '../api.service';
import { PaneService } from '../pane.service';

@Component({
  selector: 'app-allchat',
  templateUrl: './allchat.component.html',
  styleUrls: ['./allchat.component.css']
})
export class AllchatComponent implements OnInit {

  @ViewChild("paneBodyElement") paneBodyElement: ElementRef;
  @ViewChild("textInputElement") textInputElement: ElementRef;

  msgInput:string = "";
  newAllchatAddedSubscription: Subscription;

  constructor(
    public _allchat: AllchatService,
    public _api: ApiService,
    public _pane: PaneService,
  ) {
    console.log("allchat componenent::constructor()")
    this._allchat.unreadCount = 0
  }

  ngOnInit(): void {
    console.log("allchat componenent::ngOnInit()")
    this.focusOnInput()
    this.newAllchatAddedSubscription = this._allchat.newAllchatAdded.subscribe(()=>{
      setTimeout(()=>{
        this.scrollPaneToBottom()
      }, 25);
    })
  }

  ngOnDestroy()	{
    this.newAllchatAddedSubscription.unsubscribe();
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

}
