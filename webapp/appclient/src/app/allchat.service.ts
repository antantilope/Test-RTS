
import { Injectable } from '@angular/core';
import { Subject, Subscription } from 'rxjs'

import { ApiService } from './api.service';
import { AllChatMessage } from "./models/allchat-message.model"
import { PaneService } from './pane.service';


@Injectable({
  providedIn: 'root'
})
export class AllchatService {

  private maxMessages = 75;
  private maxNotificationCount = 9
  public unreadCount = 0;
  public messages: AllChatMessage[] = []

  private pubmsgEventSubscription: Subscription
  public newAllchatAdded: Subject<void> = new Subject()

  constructor(
    private _api: ApiService,
    private _pane: PaneService
  ) {
    this.pubmsgEventSubscription = this._api.pubmsgEvent.subscribe((message: AllChatMessage) => {
      this.messages.push(message)
      if (this.messages.length > this.maxMessages) {
        this.messages = this.messages.slice(
          this.messages.length - this.maxMessages,
          this.messages.length
        );
      }
      if(!this._pane.allChatPaneVisible) {
        const nextCt = this.unreadCount + 1
        this.unreadCount = Math.min(nextCt, this.maxNotificationCount)
      }
      this.newAllchatAdded.next()
    })
  }

  resetUnreadCount() {
    this.unreadCount = 0;
  }
}
