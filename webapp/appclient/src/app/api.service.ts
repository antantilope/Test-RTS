
import { Injectable } from '@angular/core'
import { HttpClient } from '@angular/common/http';
import { io } from 'socket.io-client'
import { Subject } from 'rxjs'

import { StartCountdownPayload } from './models/startcountdown-payload.model'
import { AllChatMessage } from './models/allchat-message.model';
import { FrameData } from './models/apidata.model';


@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private socket: any

  private EVENT_FRAMEDATA: string = "framedata"
  public frameDataEvent: Subject<void> = new Subject()
  public frameData: FrameData | null = null

  public lastShockwaveFrame : number | null = null

  private EVENT_STARTCOUNTDOWN: string = "startcountdown"
  public startCountdownEvent: Subject<StartCountdownPayload> = new Subject()

  private EVENT_SIGKILL: string = "sigkill"
  public sigkillEvent: Subject<void> = new Subject()

  private EVENT_PUBMSG = "pubmsg"
  public pubmsgEvent: Subject<AllChatMessage> = new Subject()

  constructor(
    private _http: HttpClient,
  ) {
    const url: string = document.location.origin.replace(/^https?/, 'ws')
    console.log("ApiService::constructor connecting to socket server on " + url)
    this.socket = io(url)

    this.socket.on("connect", () => {
      console.log("Socket Connected!")
    })

    this.socket.on(this.EVENT_FRAMEDATA, (data: FrameData) => {
      this.frameData = data
      this.frameDataEvent.next()
      if(data.game_frame % 400 === 0) {
        console.log({framedata: data})
      }
    })

    this.socket.on(this.EVENT_STARTCOUNTDOWN, (data: StartCountdownPayload) => {
      this.startCountdownEvent.next(data)
    })

    this.socket.on(this.EVENT_SIGKILL, ()=>{
      this.sigkillEvent.next()
      setTimeout(() => {
        location.reload()
      }, 750);
    })

    this.socket.on(this.EVENT_PUBMSG, (message: AllChatMessage)=>{
      this.pubmsgEvent.next(message);
    })
  }

  public async sendPublicMessage(msg: string) {
    this.socket.emit(this.EVENT_PUBMSG, msg)
  }

  public async get(url:string) {
    return this._http.get(url).toPromise();
  }

  public async post(url:string, data: any){
    return this._http.post(url, data).toPromise();
  }


}
