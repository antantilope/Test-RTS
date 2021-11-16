
import { Injectable } from '@angular/core';
import { io } from 'socket.io-client';


@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private socket;

  public EVENT_FRAMEDATA: string = "framedata";

  constructor() {
    const url: string = document.location.origin.replace(/^https?/, 'ws');
    console.log("ApiService::constructor connecting to socket server on " + url);
    this.socket = io(url);

    this.socket.on(this.EVENT_FRAMEDATA, data => {
      console.log({framedata: data});
    })
  }
}
