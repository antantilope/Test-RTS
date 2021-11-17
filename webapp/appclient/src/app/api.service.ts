
import { Injectable } from '@angular/core';
import { io } from 'socket.io-client';
import { Subject } from 'rxjs';

import { StartCountdownPayload } from './models/startcountdown-payload.model';


@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private socket;

  private EVENT_FRAMEDATA: string = "framedata";

  private EVENT_STARTCOUNTDOWN: string = "startcountdown";
  public startCountdownEvent: Subject<StartCountdownPayload> = new Subject();

  constructor() {
    const url: string = document.location.origin.replace(/^https?/, 'ws');
    console.log("ApiService::constructor connecting to socket server on " + url);
    this.socket = io(url);

    this.socket.on(this.EVENT_FRAMEDATA, data => {

    });

    this.socket.on(this.EVENT_STARTCOUNTDOWN, (data: StartCountdownPayload) => {
      this.startCountdownEvent.next(data);
    });

  }
}
