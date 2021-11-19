
import { Component } from '@angular/core'

import { TakeoverService } from './takeover.service'



@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'voidstar'

  constructor(
    public takeover: TakeoverService,
  ) {
    console.log("AppComponent::constructor")
  }

  ngAfterViewInit():void {
    console.log("AppComponent::ngAfterViewInit")

  }

  ngOnDestroy() {
    console.log("AppComponent::ngOnDestroy")
  }



}
