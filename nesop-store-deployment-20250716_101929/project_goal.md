I want to create a fake store that staff at my business can use to trade a fake currency in exchange for company swag.

I want this webpage to reference a .csv file hosted on a network share so that our non technical accounting team can manage the currency manually on the backend. For now we can reference a local .csv file. We might use an actual database later, but this is the request and this is an internal only tool.

I want the webpage to use only HTML, CSS and JavaScript. I want it to use a modern layout with a clean sleek design and a light color theme with blue accents.

I need the following:

Ability for users to log in and check their account balance. For now we can use another local .csv file with some testing username and passwords and we will build an auth system later.

Ability for users to add items to their cart and checkout. Checking out should reduce the appropriate amount of currency from their balance and send their order as an email to a specific email address. The email should include the items they have ordered and their name.