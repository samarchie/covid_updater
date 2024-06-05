import os, random, slack_sdk, slack_sdk.errors, socket, textwrap, warnings, dotenv

GREETINGS = ["Kia ora!", "Howdy partner.", "G'day mate.", "What up g? :sunglasses:", "Ugh finally, this shit is done.", "Kachow! :racing_car:", "Kachigga! :racing_car:", "Sup dude.", "Woaaaaahhhh, would you look at that!", "Easy peasy.", "Rock on bro. :call_me_hand:", "Leshgoooooo!", "Let's get this bread!", "You're doing great dude. :kissing_heart:", "Another one bits the dust...", "Sup, having a good day?", "Yeeeeeeehaw cowboy! :face_with_cowboy_hat:"] 
HAPPY_EMOJIS = [":tada:", ":cheering-bec:", ":smiley_mitch:", ":ecstatic_tom:", ":partying_face:", ":happy-patrick:", ":happy_tom:", ":dabtom:"]
SAD_EMOJIS = [":sad_will:", ":sad_willandluci:", ":cry:", ":disappointed_relieved:", ":angywill:"]

_ = dotenv.load_dotenv()
SLACK_TOKEN = os.getenv('SLACK_TOKEN')

def post_message(where_to_post, message_type, identifier=None, message=None, greet=True, silent_usernames=None, emojis=False):
    """
    Posts a message to a Slack Channel or User.
    
    Parameters
    ----------
    where_to_post: String
        A string representing the channel or person's name to post/directly message to. Note: if you wish to post to a channel, a hashtag ("#") must be placed at the start of the string, otherwise it is assumed that the message
    message_type : String
        A string representing what type of message this post should be. There are currently three options: Information, Failure and Success. Each one will post a different amount of blocks, with differnt styles of wording within them.
    identifier: String
        A string that will be used in the header to help identify which simulation the message is referring to. It is recommended that the length of the identifier is kept under 100 characters in order to display the header on one line.
    message: String
        If the message_type is Information or Failure, the message will be used in a section below a divider and will typically be a informative message or an error traceback for the two message_types respectively. 
    greet: Bool
        If True, post a cheerful greeting before the message.
    silent_usernames: String, List of Strings or None
        If silent_usernames is specified, then the message is posted to the channel (irrelevant if public or private) but only the silent_users can see the message.
    emjois: Bool 
        If True, the message_type will be wrapped with 2 appropiate emojis on either side. Otherwise, no emjois will be printed.

    Returns
    -------
    None : No parameters are outputted
    
    """

    # Start up the client to post to
    client = slack_sdk.WebClient(token=SLACK_TOKEN)
    
    # If it is not a channel, grab the user's ID instead to DM them
    if not where_to_post.startswith("#"):
        where_to_post = get_users_information_from_name(where_to_post, "id", client)

    # Generate the content used in the message
    header, header_lines = generate_header(message_type, identifier, emojis) 
    blocks = generate_blocks(message_type, message, header_lines, greet)

    try:
        # Send a quiet message if requested
        if silent_usernames != None:
            if type(silent_usernames) == str:
                silent_user_ids = [get_users_information_from_name(silent_usernames, "id", client)]
            elif type(silent_usernames) == list:
                silent_user_ids = [get_users_information_from_name(silent_username, "id", client) for silent_username in silent_usernames]
            for silent_user_id in silent_user_ids:
                _ = client.chat_postEphemeral(channel=where_to_post, blocks=blocks, user=silent_user_id, text=header)
        # Or send it to a public/private channel
        else:
            _ = client.chat_postMessage(channel=where_to_post, blocks=blocks, text=header)
    
    except slack_sdk.errors.SlackApiError as error:
        warnings.warn("The message could not be posted to slack. Error: {}".format(error.response["error"]), UserWarning)


def generate_header(message_type, identifier, emojis):
    """
    Generates a header, or a list of headers depending on the length of the header, to be used to quickly summarise the message to be posted to the Slack channel or User.
    
    Parameters
    ----------
    message_type : String
        A string representing what type of message this post should be. There are currently three options: Information, Failure and Success. Each one will post a different amount of blocks, with differnt styles of wording within them.
    identifier: String
        A string that will be used in the header to help identify which simulation the message is referring to. It is recommended that the length of the identifier is kept under 100 characters in order to display the header on one line.
    emjois: Bool 
        If True, the message_type will be wrapped with 2 appropiate emojis on either side. Otherwise, no emjois will be printed.
   
    Returns
    -------
    header: String
        A sentence split into 3 main parts - 1) the message_type surrounded by emojis (if applicable), 2) the identifier and 3) the name of the machine the code is currently running on
    header_lines: List of Strings
        If the header is equal to or above 150 characters long, then the string is split into multiple strings and returned in a list.
    
    """

    # If no identifier is given, then do not produce a header
    if identifier == None:
        return "", None

    # Add some emojis to the header to spice it up if the user has requested so.
    if emojis:
        if message_type == 'Success':
            emojis = random.sample(HAPPY_EMOJIS, 2)
            header = f'{emojis[0]} {message_type.title()} {emojis[1]} |  {identifier}  |  Running on {socket.gethostname()}'
        elif message_type == "Failure":
            emojis = random.sample(SAD_EMOJIS, 2)
            header = f'{emojis[0]} {message_type.title()} {emojis[1]} |  {identifier}  |  Running on {socket.gethostname()}'
        else:
            header = f'{message_type.title()} |  {identifier} |  Running on {socket.gethostname()}'
    else:
        header = f'{message_type.title()} |  {identifier} |  Running on {socket.gethostname()}'

    # Unfortunately, there is a 150 character limit on the header length, so split and send multiple if that is the case!
    header_lines = [header]
    if len(header) > 150:
        header_lines = textwrap.wrap(header, width=100, break_long_words=False, break_on_hyphens=False)

    return header, header_lines


def generate_blocks(message_type, message, header_lines, greet):
    """
    Generates the blocks, a JSON-based list of structured blocks presented as URL-encoded strings, to be used to display message to be posted to the Slack channel or User.

    Example:
    [{"type": "section", "text": {"type": "plain_text", "text": "Hello world"}}]
    
    Parameters
    ----------
    message_type : String
        A string representing what type of message this post should be. There are currently three options: Information, Failure and Success. Each one will post a different amount of blocks, with differnt styles of wording within them.
    identifier: String
        A string that will be used in the header to help identify which simulation the message is referring to. It is recommended that the length of the identifier is kept under 100 characters in order to display the header on one line.
    greet: Bool
        If True, post a cheerful greeting before the message.

    Returns
    -------
    blocks: List
        A JSON-based list of structured blocks presented as URL-encoded strings
    
    """

    greeting = random.sample(GREETINGS, 1)[0] + " " if greet else ""

    blocks=[]

    if header_lines != None:
        for header_line in header_lines:
            blocks.append({"type": "header", 
                            "text":
                                {"type": "plain_text", 
                                "text": header_line, 
                                "emoji": True}
                            })
        blocks.append({"type": "divider"})

    if message_type.title() ==  "Information":
        blocks.append({ "type": "section",
                        "text": {"type": "mrkdwn",
                                "text": greeting+message}
                        })       
    elif message_type.title() == "Success":
        blocks.append({"type": "section",
                        "text": {"type": "mrkdwn",
                                "text": greeting+"It is my pleasure to inform you that the procedure has been a success."}
                        })       
    elif message_type.title() == "Failure": 
        # Strip away any output in stdout before the error message begins
        lookout_phrase = "Traceback (most recent call last):"
        if lookout_phrase in message:
            message = message[message.index(lookout_phrase)+len(lookout_phrase):].strip()

        blocks.extend([{"type": "section",
                        "text": {"type": "mrkdwn",
                                "text": f"{greeting}It is unfortunate that I must inform that something went wrong."}
                        },
                    {"type": "section",
                    "text": {"type": "mrkdwn",
                            "text": "*Error Traceback:*"}
                    },
                    {"type": "divider"},
                    {"type": "section",
                    "text": {"type": "mrkdwn",
                            "text": message.strip("\r\n")}
                    }])
    
    return blocks


def post_files(where_to_post, filenames, message, greet=True):
    """
    Posts files to a Slack Channel or User.
    
    Parameters
    ----------
    where_to_post: String
        A string representing the channel or person's name to post/directly message to. Note: if you wish to post to a channel, a hashtag ("#") must be placed at the start of the string, otherwise it is assumed that the message
    filenames : String or List of Strings
        A string representing the filepath to the file to be posted, or a list of strings to post.
    message: String
        A text message to display above the file in the Slack channel, primarily used to describe or introduce the file uploaded. 
    greet: Bool
        If True, post a cheerful greeting before the message.

    Returns
    -------
    None : No parameters are outputted
    
    """

    # Start up the client to post to
    client = slack_sdk.WebClient(token=SLACK_TOKEN)
    
    # If it is not a channel, grab the user's ID instead to DM them
    if not where_to_post.startswith("#"):
        where_to_post = get_users_information_from_name(where_to_post, "id", client)

    # Add a greeting if the user asked for one
    greeting = random.sample(GREETINGS, 1)[0] + " " if greet else ""
    
    # In case only one file was passed in, then chuck the string into a list by itself
    if type(filenames) == str:
        filenames = [filenames]

    try:
        inital_comment_sent = False
        for filename in filenames:
            if not inital_comment_sent:
                # Send the files with the initial comment as it has not been sent yet
                _ = client.files_upload(channels=where_to_post, initial_comment=greeting+message, file=filename)
                inital_comment_sent = True
            else:
                # Otherwise send just the files
                _ = client.files_upload(channels=where_to_post, file=filename)
    
    except slack_sdk.errors.SlackApiError as error:
        warnings.warn("The file {} could not be posted to slack. Error: {}".format(filename, error.response["error"]), UserWarning)


def get_users_information_from_name(user_name, wanted_information, client):
    """
    Retrieves a specified *wanted_information* attribute of a user by the name of *user_name*. The *user_name* can be the full name of the individual or their display name. If no exact matches are found, then possible matches are considered by their full name, display name and by first name and surname.
    
    Parameters
    ----------
    user_name : String
        A string representing the name of the user to be contacted, e.g. 'Sam Archie' or 'tom'. 
    wanted_information: String
        A string representing the  
    greet: Bool
        If True, post a cheerful greeting before the message.
   
    Returns
    -------
    None : No parameters are outputted
    
    """

    # Change the user_name to title case so we can == compare it with the other fields
    user_name = user_name.title()
    
    # Create lists for exact and possible matches
    exact_matches = []
    possible_matches = []

    # Query the client for a list of members
    members = client.users_list()["members"]

    for member in members:
        # If inactive user or is a bot then continue to the next
        if member["deleted"] or member["is_bot"]:
            continue
        
        # Check for exact results of id! E.g. the user passed in the actual id of the person, so why bother looking any further!
        if member.get("id", "") == user_name:
            return user_name
        
        # Check for exact mataches against the profile
        profile_details = member.get("profile", {})
        if profile_details.get("real_name", "").title() == user_name:
            exact_matches.append(member)
        elif profile_details.get("display_name", "").title() == user_name:
            exact_matches.append(member)
        elif profile_details.get("real_name_normalized", "").title() == user_name:
            exact_matches.append(member)
        elif profile_details.get("display_name_normalized", "").title() == user_name:
            exact_matches.append(member)

        # Check for possible matches
        elif user_name in member.get("id", ""):
            possible_matches.append(member)
        elif user_name in profile_details.get("real_name", "").title():
            possible_matches.append(member)
        elif user_name in profile_details.get("display_name", "").title():
            possible_matches.append(member)
        elif user_name in profile_details.get("real_name_normalized", "").title():
            possible_matches.append(member)
        elif user_name in profile_details.get("display_name_normalized", "").title():
            possible_matches.append(member)
        elif user_name.split(" ")[0] in profile_details.get("first_name", "").title():
            possible_matches.append(member)
        elif user_name.split(" ")[-1] in profile_details.get("last_name", "").title():
            possible_matches.append(member)

    
    if len(exact_matches) == 1:
        # Best case scenario!
        chosen_user_details = exact_matches[0]

    elif len(exact_matches) > 1:
        print(f"Multiple users detected with the user_name '{user_name}'. Please define which user you are indending to post to from the current list:\n")
        counter = 1
        for exact_match in exact_matches:
            print(f"Possible Match {counter}:")
            print(exact_match, end="\n")
            counter +=1 
        correct_individual_number = int(input(f"From this list, which number (from 1 to {len(exact_matches)}) was the user you were wishing to post locate?"))
        chosen_user_details = exact_matches[correct_individual_number - 1]
    
    else:
        if len(possible_matches) == 1:
            chosen_user_details = possible_matches[0]
        else:
            print(f"No exact matches were found for '{user_name}. However, multiple possible matches exists. Please define which user you are indending to post to from the current list:\n")
            counter = 1
            for possible_match in possible_matches:
                print(f"Possible Match {counter}:")
                print(possible_match, end="\n")
                counter +=1 
            correct_individual_number = int(input(f"From this list, which number (from 1 to {len(possible_matches)}) was the user you were wishing to post locate?"))
            chosen_user_details = possible_matches[correct_individual_number - 1]

    # Now grab the wanted_information from the chosen_user_details
    if wanted_information in chosen_user_details:
        chosen_information = chosen_user_details[wanted_information]
    elif wanted_information in chosen_user_details["profile"]:
        chosen_information = chosen_user_details["profile"][wanted_information]
    else:
        keys = sorted(set(list(chosen_user_details.keys()) + list(chosen_user_details["profile"].keys())))
        correct_wanted_information = input(f"The user name {user_name} was found but the wanted information {wanted_information} is not within the recorded details. Please choose from the following:\n {keys}")
        if correct_wanted_information in chosen_user_details:
            chosen_information = chosen_user_details[correct_wanted_information]
        elif correct_wanted_information in chosen_user_details["profile"]:
            chosen_information = chosen_user_details["profile"][correct_wanted_information]
    
    return chosen_information
