import { Component, OnInit } from '@angular/core';
import { TakeoverService } from '../takeover.service';


@Component({
  selector: 'app-takeover',
  templateUrl: './takeover.component.html',
  styleUrls: ['./takeover.component.css']
})
export class TakeoverComponent implements OnInit {

  constructor(
    public takeover: TakeoverService,
  ) {
    console.log("TakeoverComponent::constructor");
  }

  ngOnInit(): void {
  }

}
