
import { Injectable } from '@angular/core';
import { Subject, Subscription } from 'rxjs'

import { ApiService } from './api.service';
import { AllChatMessage } from "./models/allchat-message.model"




@Injectable({
  providedIn: 'root'
})
export class AllchatService {

  private maxMessages = 25;
  public unreadCount = 3;
  public messages: AllChatMessage[] = []

  private pubmsgEventSubscription: Subscription
  public newAllchatAdded: Subject<void> = new Subject()

  constructor(
    private _api: ApiService,
  ) {
    this.pubmsgEventSubscription = this._api.pubmsgEvent.subscribe((message: AllChatMessage) => {
      this.messages.push(message)
      if (this.messages.length > this.maxMessages) {
        this.messages = this.messages.slice(
          this.messages.length - this.maxMessages,
          this.messages.length
        );
      }
      this.newAllchatAdded.next()
    })
  }
}
