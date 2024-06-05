<br />
<p align="center">
  <img src="docs/covid-banner.png">
  </a>

  <h3 align="center">Covy</h3>

  <p align="center">
    Your friendly neighhbourhood Python bot to communicate and update you of any changes in New Zealands locations of interest and daily Covid-19 cases.
  </p>
</p>
<br />

### About Covy

Back when Covid-19 broke out, I hated tuning into the news and hearing all the unfortunate stories. I needed someone to summarise if I was anywhere near danger and how quickly cases were rising. 

Covy scrapes data from the government website (Ministry of Health) for updates in case numbers, and also from the the University of Canterbury's website (where I was studying at the time) to update me on any classes or halls that had confirmed cases.

The scraped data, at every 10 minute interval, is then processed and checked against previously known locations. For new events, a notification with a breakdown of data is sent to me via Slack, where I predominanantly worked


### Getting Started

1. Clone this repository
```
git clone git@github.com:samarchie/covy.git
```

2. Create a Slack API App, named Cody, to allow external programs (such as Python) to post messages to Slack. To do so, create the bot through a [Slack App](https://api.slack.com/apps), choose 'Bots' and 'Permissions' for the 'Features and Functionality', **and most importantly**: set the OAuth & Permissions Bot Scope to at least allow: 

| Bot Token Scope   | Description                                       |
|-------------------|---------------------------------------------------|
| chat:write        | Send messages as @cody                            |
| chat:write.public | Send messages to channels @cody isn't a member of |
| files:write       | Upload, edit, and delete files as Cody            |
| im:write          | Start direct messages with people                 |
| users:read        | View people in a workspace                        |

3. From the Slack App webpage, locate the 'Bot User OAuth Token' on the OAuth & Permissions page, and add it to the ```.env``` file with the ```SLACK_TOKEN``` key.
The token wil be in the form alike: ```xoxb-17653672481-19874698323-pdFZKVeTuE8sk7oOcBrzbqgy```


4. In your project virtual environment or global Python environment, install the required packages in ```requirements.txt```.
```
pip install -r requirements.txt
```

5. In a terminal with the working directory set as the covy folder, simply run:
```sh
python3 covy.py
```

<br>

### Things to Remember

This is an API service, and it has its own rate limits as defined by the [Slack Rate Limits](https://api.slack.com/docs/rate-limits)

- Posting message: Varies but most likely 1 message per second

- Posting message hidden to 1 person: 100 messages per minute

- Posting files: 20 files per minute

<br>

> I wish you all the best in using Covy to its full extent, and that you never recieve Covid :heart::mask:
> Yours truly, Sam Archie
