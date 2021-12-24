"""
CLI command that deals with wiki related commands
"""

# Imports from wa_cli
from wa_cli.utils.logger import LOGGER

def run_post(args):
    """The `post` command will create a post template for the Wisconsin Autonomous Wiki.

    The Wiki is located at [WisconsinAutonomous.github.io](https://WisconsinAutonomous.github.io) and
    is a jekyll site that creates website pages from markdown code.

    For information on creating a new post, see [this page](https://wisconsinautonomous.github.io/posts/writing-a-new-post/).

    This command a generated post template similar to the following:

    ```markdown
    ---
    title: New Post
    author: Your Name
    date: 2021-01-11 00:00:00 -0600
    categories: [Introduction, Wiki Tutorials]
    tags: [tutorials, templates, non-technical]
    ---

    This is a template for a new post for this site. Feel free to copy this markdown directly to your new file.

    ## Setup Guide


    ## Support

    Contact [Your Name](mailto:wiscid@wisc.edu) for any questions or concerns regarding the contents of this post.

    ## See Also

    Stay up to date with our technical info by following our [blog](https://wa.wisc.edu/blog).

    Follow us on [Facebook](https://www.facebook.com/wisconsinautonomous/), [Instagram](https://www.instagram.com/wisconsinautonomous/), and [LinkedIn](https://www.linkedin.com/company/wisconsin-autonomous/about/)!

    ![WA Logo](/assets/img/logos/wa-white.png){: .left height="100"}
    ![Wisconsin Crest](/assets/img/logos/uw-crest.png){: .right height="100"}
    ```
    """

    LOGGER.debug("Running 'wiki post' entrypoint...")

    # The template markdown
    template = """---
title: {title}
author: {author}
date: {date} {time} -0600
categories: {categories}
tags: {tags}
---

This is a template for a new post for this site. Feel free to copy this markdown directly to your new file.

## Setup Guide


## Support

Contact [{author}](mailto:{email}) for any questions or concerns regarding the contents of this post.

## See Also

Stay up to date with our technical info by following our [blog](https://wa.wisc.edu/blog).

Follow us on [Facebook](https://www.facebook.com/wisconsinautonomous/), [Instagram](https://www.instagram.com/wisconsinautonomous/), and [LinkedIn](https://www.linkedin.com/company/wisconsin-autonomous/about/)!

![WA Logo](/assets/img/logos/wa-white.png){{: .left height="100"}}
![Wisconsin Crest](/assets/img/logos/uw-crest.png){{: .right height="100"}}
    """

    fmt = {}

    # Parse the arguments
    fmt['title'] = args.title
    fmt['author'] = args.author
    fmt['categories'] = str(args.categories)
    fmt['tags'] = str(args.tags)
    fmt['email'] = args.email

    # Determine the data and such
    from datetime import datetime
    now = datetime.now()
    fmt['date'] = now.strftime("%Y-%m-%d")
    fmt['time'] = now.strftime("%H:%M:%S")
    
    # Format the existing template with the passed args
    template = template.format(**fmt)
    
    # Save the file
    filename = f"{fmt['date']}-{fmt['title'].replace(' ', '-').lower()}.md"
    LOGGER.debug(f"Going to write template post to {filename}...")
    if not args.dry_run:
        LOGGER.info(f"Saving template post to {filename}...")
        with open(filename, 'w') as f:
            f.write(template)
        LOGGER.info(f"Saved template post to {filename}...")

def init(subparser):
    """Initializer method for the `wiki` entrypoint.

    This entrypoint serves as a mechanism for running helpers that relate to
    the wiki website at [WisconsinAutonomous.github.io](https://WisconsinAutonomous.github.io).

    Current subcommands:

        - `post`: Creates a template post.
    """

    # Create some entrypoints for additional commands
    subparsers = subparser.add_subparsers(required=False)

    # Post subcommand
    post = subparsers.add_parser("post", description="Creates a template post.")
    post.add_argument("--title", type=str, help="The title of the post.", required=True)
    post.add_argument("--author", type=str, help="The author to use for the post.", default="Wisconsin Autonomous")
    post.add_argument("--category", type=str, dest="categories", action="append", help="The categories to mark on the post", default=[])
    post.add_argument("--tag", type=str, dest="tags", action="append", help="The tags to mark on the post", default=[])
    post.add_argument("--email", type=str, help="Email to use in the post.", default="wisconsinautonomous@studentorg.wisc.edu")
    post.set_defaults(cmd=run_post)
