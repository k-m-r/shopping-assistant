# Shopping Assistant

Started this project mostly to learn about MCP.
Along the way I thought this will be a good opportunity for me to automate some of the cart building process.

Leveraging the Public API's provided by Kroger

The way I am planning to implement the shopping assistant is  :

- We do most of our shopping from [Kroger](https://www.kroger.com/). Starting with integration only to Kroger
- There can be two broad categories of purchase.

  - Items that we buy every week (regulars). Example : milk, banana
  - Items that are bought on a need basis. Example Ice cream, butter
- I am planning to maintain a list for regular items and an option to provide an natural language input for additional items.
- To start with the list may look like a <item (milk)>  < quantity>(Optional)
- If quantity is not mentioned, program will assume the default quantity as one
- As we know the items we buy, I may provide a reference to the items we usually buy. example "milk" means Kroger® 2% Reduced Fat Milk Gallon


## Future enhancements

- add logic to compare the unit price for items and decide which one to buy. For example is half gallon milk is on sale, choose that over gallon milk
- calculate the total for the items added to the cart


## Development approach
As I started this project mostly for learning purpose, I am not planning to use on any AI coding assistants in the IDE
The way I am working is 
- decide what to implement
- iterate over the plan with the help of Google Gemini
- Use Gemini web interface to get code snippets


For the current use case I am working on , LLM is not mandatory
I am planning to start another project to play around with LLM more


## References
[Kroger Developer Marketplace](https://developer.kroger.com/documentation/public/getting-started/quick-start)



