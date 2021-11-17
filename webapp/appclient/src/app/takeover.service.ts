
import { Injectable } from '@angular/core';
import { Subscription } from 'rxjs';

import { ApiService } from "./api.service";
import { StartCountdownPayload } from './models/startcountdown-payload.model';


@Injectable({
  providedIn: 'root'
})
export class TakeoverService {

  public showTakeover: boolean = true;
  private defaultMessage: string = "waiting for server...";
  public takeoverMessage: string = this.defaultMessage;

  private startCountdownEventSubscription: Subscription;
  private frameDataEventSubscription: Subscription;

  constructor(
    private _api: ApiService,
  ) {
    console.log("TakeoverService::constructor");

    this.startCountdownEventSubscription = this._api.startCountdownEvent.subscribe(
      (data: StartCountdownPayload) => {
        console.log("startCountdownEvent " + JSON.stringify(data));
        if(data.game_start_countdown > 0) {
          this.showTakeover = true;
          this.takeoverMessage = `Game Starting in ${data.game_start_countdown}`;
        } else {
          this.showTakeover = false;
          this.takeoverMessage = this.defaultMessage;
        }
      }
    );

    this.frameDataEventSubscription = this._api.frameDataEvent.subscribe((data: any) => {
      this.showTakeover = false;
      this.takeoverMessage = this.defaultMessage;
    });

  }

  ngOnDestroy() {
    console.log("TakeoverService::ngOnDestroy");
    this.startCountdownEventSubscription.unsubscribe();
    this.frameDataEventSubscription.unsubscribe();
  }

}
