import { Injectable } from '@angular/core';



export class QuoteDetails {
  lines: string[]
  author?: string
}


@Injectable({
  providedIn: 'root'
})
export class QuoteService {

  private quotes: QuoteDetails[] = [
    {
      lines:[
        "Victory has a thousand fathers, but defeat is an orphan."
      ],
      author: "John F. Kennedy"
    },
    {
      lines:[
        "Never confuse a single defeat with a final defeat."
      ],
      author: "F. Scott Fitzgerald",
    },
    {
      lines:[
        "Failure is the condiment that gives success its flavor."
      ],
      author: "Truman Capote",
    },
    {
      lines:[
        "Live by the death ray, die by the death ray.",
      ],
    },
    {
      lines:[
        "Death may be the greatest of all human blessings."
      ],
      author: "Socrates",
    },
    {
      lines:[
        "Everyone has a plan 'til they get punched in the mouth."
      ],
      author: "Mike Tyson",
    },
    {
      lines:[
        "More is lost by indecision than wrong decision."
      ],
      author: "Tony Soprano",
    },
    {
      lines: [
        "The Universe is under no obligation to make sense to you.",
      ],
      author: "Neil deGrasse Tyson",
    },
    {
      lines: [
        "Only the dead have seen the end of the space war.",
      ],
      author: "Space General Pattontron",
    },
    {
      lines: [
        "All space warfare is based on space deception.",
      ],
      author:"Sir Space Bot The V3.773.22",
    },
    {
      lines: [
        "You may find youself in a decisively good or bad position",
        "if you fire first in a space duel. It depends."
      ],
      author: "CUSIM 4-10.32",
    },
    {
      lines: [
        "Space fuel is terribly flammible. Be carful when operating a fueled spacecraft."
      ],
      author: "CUSIM 1-232.1",
    },
    {
      lines: [
        "Space fuel is terribly flammible. Be carful when operating a fueled spacecraft."
      ],
      author: "CUSIM 1-232.1",
    },
  ]

  constructor() { }

  public getQuote(): QuoteDetails {
    return this.quotes[Math.floor(Math.random()* this.quotes.length)]
  }
}
