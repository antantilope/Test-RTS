
import { Injectable } from '@angular/core'
import { io } from 'socket.io-client'
import { Subject } from 'rxjs'

import { StartCountdownPayload } from './models/startcountdown-payload.model'


@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private socket: any

  private EVENT_FRAMEDATA: string = "framedata"
  public frameDataEvent: Subject<any> = new Subject()
  public frameData: any = null

  private EVENT_STARTCOUNTDOWN: string = "startcountdown"
  public startCountdownEvent: Subject<StartCountdownPayload> = new Subject()

  constructor() {
    const url: string = document.location.origin.replace(/^https?/, 'ws')
    console.log("ApiService::constructor connecting to socket server on " + url)
    this.socket = io(url)

    this.socket.on(this.EVENT_FRAMEDATA, (data: any) => {
      this.frameData = data
      this.frameDataEvent.next(data)
      if(data.game_frame % 500 === 0) {
        console.log({framedata: data})
      }
    })

    this.socket.on(this.EVENT_STARTCOUNTDOWN, (data: StartCountdownPayload) => {
      this.startCountdownEvent.next(data)
    })

  }
}
