#!/usr/bin/env python3
# Author: Silas Cutler (p1nk.io)
# cli_tool.py

import click
import os
import requests
import json
from datetime import datetime, timedelta, timezone
from tabulate import tabulate
import textwrap

API_URL = "https://ecrime.ch/api/v1"
API_KEY = os.getenv('ECRIME_API_KEY', None)

def callAPI(method, url, json=None):
    API_HEADERS = { "X-API-Key" : API_KEY}
    # print(url)
    try:
        if method == "GET":
            res = requests.get(url, headers=API_HEADERS)
        elif method == "POST":
            res = requests.post(url, headers=API_HEADERS, json=json)
    except Exception as e:
        print(f'[!] Error calling API: {e}')
        return False, ""

    if res.status_code == 403:
        print(f'[X] HTTP 403 - your account is unauthorized to make this request: {url}')
        return False, res

    try:
        response = res.json()
    except Exception as e:
        print(f'[!] Error converting response to json: {e}')
        return False, res


    # Parse status codes in JSON response
    if int(response.get('status', 0)) == 200:
        return True, response
    elif int(response.get('status', 0)) == 403:
        print(f'[X] 403 - your account is unauthorized to make this request: {url}')
        return False, response
    else:
        print(f'[!] Likely error: response: {response.get('message', response)}')
        print(response)

        return False, response



@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """A CLI tool to interact with the eCrime.ch."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@click.command()
def login():
    """Test authentication"""
    API_HEADERS = {"X-API-Key" : API_KEY}
    response = callAPI('GET', f"{API_URL}/login/")

    click.echo(f"[+] Login: {response.get('message')}")


@click.command()
@click.option('--event_id', default=None, help="View specific id.")
@click.option('--search', default=None, help="Search tracked events")
@click.option('--from_timestamp', default=None, help="The start timestamp in YYYY-MM-DD format (e.g., '2023-01-01")
@click.option('--to_timestamp', default=None, help="The end timestamp in YYYY-MM-DD format (e.g., '2023-12-31")
@click.option('--outjson', is_flag=True, default=False, help="Output JSON response.")
def events(event_id, search, from_timestamp, to_timestamp,outjson):
    """Events - List / Search - (Defaults to last 30 days)"""
    time_params = "from/{}/to/{}/"

    # Errors when timestamp set
    if from_timestamp is None:
        from_timestamp = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    if to_timestamp is None:
        to_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    time_params = time_params.format(from_timestamp, to_timestamp)

    if event_id != None:
        _, response = callAPI('GET', f"{API_URL}/events/view/{event_id}/")

        if _:

            if outjson == True:
                click.echo(json.dumps(response.get('data')))
                return True

            if len(response.get('data')) == 0:
                click.echo(f"[!] No events found for ID: {event_id}")
            else:
                if len(response.get('data')[0].get('status', [])) == 0:
                    click.echo(f"[!] No events found for ID: {event_id}")
                    return True

                else:
                    rec = response.get('data')[0]
                    event = []
                    ignore_keys = ['extra', 'logo', 'status']
                    for _k in rec.keys():
                        if _k in ignore_keys:
                            continue
                        val = '\n'.join(textwrap.wrap(str(rec.get(_k)), 110))
                        event.append([ _k, val])

                    click.echo(tabulate(event, tablefmt='fancy_grid'))
                    return True
        else:
            click.echo(f"[!] Error searching for event ID: {event_id}")
            return False

  
    elif search == None:
        _, response = callAPI('GET', f"{API_URL}/events/list/{time_params}")
    else:
        _, response = callAPI('GET', f"{API_URL}/events/search/{search}/{time_params}")

    if _:
        if outjson == True:
            click.echo(json.dumps(response.get('data')))
            return

        events = [[ "id", "Leak Site", "Leak Title", "Country", "First Seen"]]
        for _event in response.get('data'):
            # print(_event)
            events.append([
                _event.get("id", "-"),
                _event.get("leak_site", "-"),
                _event.get("leak_title", "-"),
                _event.get("country", "-"),
                # _event.get("name", "-"),
                _event.get("first_seen", "-"),
               
            ]) 
        click.echo(tabulate(events[1:], headers=events[0], tablefmt='fancy_grid'))
    else:
        click.echo(f"[!] Error - Unable to list/search events")
        return False



@click.command()
@click.option('--search', default=None, help="Search leaksites")
@click.option('--online', is_flag=True, default=False, help="Show online leaksites.")
@click.option('--outjson', is_flag=True, default=False, help="Output JSON response.")
def leaksites(search, online, outjson):
    """Leaksites - Search / Online"""


    if search == None:
        _, response = callAPI('GET', f"{API_URL}/leaksites/list/")
    elif online == True:
        _, response = callAPI('GET', f"{API_URL}/leaksites/list/online/")

    else:
        _, response = callAPI('GET', f"{API_URL}/leaksites/search/{search}/")


    if _:
        if outjson == True:
            click.echo(json.dumps(response.get('data')))
            return

        # Check status
        leaksite = [[ "id", "Leak Site", "Last Seen", "URL"]]
        for _site in response.get('data'):
            # print(_site)
            leaksite.append([
                _site.get("id", "-"),
                _site.get("leaksite_name", "-"),
                _site.get("last_seen", "-"),
                _site.get("url", "-"),
                
            ])
        click.echo(tabulate(leaksite[1:], headers=leaksite[0], tablefmt='fancy_grid'))
    else:
        click.echo(f"[!] Error - Unable to list/search leaksites")
        return False

@click.command()
@click.option('--actor_id', default=None, help="View Actor by ID")
@click.option('--search', default=None, help="Search actor profiles")
@click.option('--outjson', is_flag=True, default=False, help="Output JSON response.")
def actors(actor_id, search, outjson):
    """Actors - Search / Online"""

    # If Actor_ID - Pull /actors/view/:ID
    if actor_id != None:
        _, response = callAPI('GET', f"{API_URL}/actors/view/{actor_id}/")

        if _:
            # Handle JSON output and return
            if outjson == True:
                click.echo(json.dumps(response.get('data')))
                return True

            if len(response.get('data')) == 0:
                click.echo(f"[!] No actors found with ID: {actor_id}")
                return False
            else:

                rec = response.get('data')[0]
                actor = []
                ignore_keys = [ 'screenshot_image']
                print("XX")
                for _k in rec.keys():
                    if _k in ignore_keys:
                        continue
                    val = '\n'.join(textwrap.wrap(str(rec.get(_k)), 110))
                    actor.append([ _k, val])
                click.echo(tabulate(actor, tablefmt='fancy_grid'))
            return True
        else:
            click.echo(f"[!] Error searching for ID: {actor_id}")
            return False
  


    elif search != None:
        _, response = callAPI('GET', f"{API_URL}/actors/search/{search}/")

    else:
        _, response = callAPI('GET', f"{API_URL}/actors/list/")


    if _:
        # Handle JSON output and return
        if outjson == True:
            click.echo(json.dumps(response.get('data')))
            return True
            
        actors = [[ "id", "Name", "Alt Names"]]

        for _actor in response.get('data'):
            alt_names = ""
            if type(_actor.get("name_alt")) == str:
                alt_names = _actor.get("name_alt")
            elif type(_actor.get("name_alt", [])) == list:
                alt_names = ",".join(_actor.get("name_alt", []))

            actors.append([
                _actor.get("id", "-"),
                _actor.get("name", "-"),
                alt_names,
                
            ])
        click.echo(tabulate(actors[1:], headers=actors[0], tablefmt='fancy_grid',))
    else:
        click.echo(f"[!] Error - Unable to list/search actors")
        return False




cli.add_command(login)
cli.add_command(events)
cli.add_command(leaksites)
cli.add_command(actors)


if __name__ == "__main__":
    if API_KEY == None:
        print("[!] `ECRIME_API_KEY` environmental variable missing.  Please set key and try again")
    else:
        cli()