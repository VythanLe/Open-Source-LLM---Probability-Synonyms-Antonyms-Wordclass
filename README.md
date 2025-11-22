UnFinished basic LLM with the goal of making a completely free community LLM. Use the code at free will, but if you make another version link it or send it to me to update this repository with the better working version.
Currently you can run the file from the script and it should work without error. Some features like --Min[20] and --Max[] replies are broken but were fixed by a bot in another version that broke the other code (deepseek) some of the formatting needs to 
be rearranged and topic data must be implemented to properly weight probability of the words for the topic, as well as add memory for certain topics if wanted. ###ENHANCED FEATURES### need to be improved and the entire thing could be shrunken into shorter functions.


This needs it's advance features integrated: internet search integration, you can current type --internet, --python or --image to activate the unimplemented internet search/read and python or image manipulation (not generation just editing for the record).

This uses a probability algorithm of A==B, B==C, C==A for weighting dictionary words by copying their dictionary tags to eachother: Synonym 1 is synonymous with 2 and so 3 is copied because 3 is synonymous with 2, now synonymous with 1 as well. 

It works with synonyms, antonyms, wordclass pattern (noun before verb, etc), before/after patterns and start/middle/end patterns (per word to control the probability data). 

It should -
1. create missing dictionary files in the directory you run it in.
2. detect missing words and attribute their wordclass according to their surroudning KNOWN words.
3. save data.
4. training mode should recursively build the dictionary.
everything uses the same dictionary except for python and the other JSON files are for pattern data (should probably be fixed to work with the regular dictionary).

All it needs is the special features implemented and a proper "context" ruled in, so when the dictionary is fully weighted (word against word) it can properly choose a context field (conversation topic) and put that to an expert to search for specific wordtypes. 
This will avoid the reply being just weighted after pattern data but plug in the "weight" of the conversation topic to apply to the highest probability of the word order in the reply. Possibly also using a short topic based memory system or a very well structure one
like the python dictionary or a python syntax scanning tree --> dictionary format memory. Other than that it appears to be functioning fully as am LLM. 

note## Some of the other special features other than internet, python, image may be broken: chat history, emotional tone etc should be checked and improved.
