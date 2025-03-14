text='''### Specify Types of Tag\nBased on the provided Abstract Data Type (ADT) for the class `ThrillerMovie`, the following XML tags will be used to wrap relevant segments of the article:\n\n1. `<Name>`: For the title of the movie.\n2. `<PlotComplexity>`: For the complexity of the plot.\n3. `<PsychologicalDepth>`: For the exploration of psychological themes and character motivations.\n4. `<CharacterDevelopment>`: For the assessment of character development.\n5. `<TwistsAndTurns>`: For unexpected plot developments.\n6. `<Themes>`: For the central ideas and messages of the film.\n7. `<AdditionalInformation>`: For any supplementary details about the movie.\n\n### Reformatted Article\nIn the mood for a particular movie? Saw something interesting and want more? Have a favourite movie you want to recommend? Make those Movie Suggestions.\n\n# Can you recommend any films similar to <Name>\"Shutter Island\"</Name>?\n\nREQUESTING\n\nI thought <Name>Shutter Island</Name> was an amazing film. I'm a big fan of these types of <PsychologicalDepth>psychological thrillers</PsychologicalDepth>. I can't seem to find anything as good.\n\nCreate your account and connect with a world of communities.\n\n.\n\nPublic\n\nAnyone can view, post, and comment to this community\n\n## Top Posts\n\n- Reddit \n\nreReddit: Top posts of March 8, 2023\n- Reddit \n\nreReddit: Top posts of March 2023\n- Reddit \n\nreReddit: Top posts of 2023\n\n&amp;nbsp;\n\n&amp;nbsp;\n\nTOPICS\n\nInternet Culture (Viral)\n\n- Amazing\n- Animals &amp;amp; Pets\n- Cringe &amp;amp; Facepalm\n- Funny\n- Interesting\n- Memes\n- Oddly Satisfying\n- Reddit Meta\n- Wholesome &amp;amp; Heartwarming\n\nGames\n\n- Action Games\n- Adventure Games\n- Esports\n- Gaming Consoles &amp;amp; Gear\n- Gaming News &amp;amp; Discussion\n- Mobile Games\n- Other Games\n- Role-Playing Games\n- Simulation Games\n- Sports &amp;amp; Racing Games\n- Strategy Games\n- Tabletop Games\n\nQ&amp;As\n\n- Q&amp;amp;As\n- Stories &amp;amp; Confessions\n\nTechnology\n\n- 3D Printing\n- Artificial Intelligence &amp;amp; Machine Learning\n- Computers &amp;amp; Hardware\n- Consumer Electronics\n- DIY Electronics\n- Programming\n- Software &amp;amp; Apps\n- Streaming Services\n- Tech News &amp;amp; Discussion\n- Virtual &amp;amp; Augmented Reality\n\nPop Culture\n\n- Celebrities\n- Creators &amp;amp; Influencers\n- Generations &amp;amp; Nostalgia\n- Podcasts\n- Streamers\n- Tarot &amp;amp; Astrology\n\nMovies &amp; TV\n\n- Action Movies &amp;amp; Series\n- Animated Movies &amp;amp; Series\n- Comedy Movies &amp;amp; Series\n- Crime, Mystery, &amp;amp; Thriller Movies &amp;amp; Series\n- Documentary Movies &amp;amp; Series\n- Drama Movies &amp;amp; Series\n- Fantasy Movies &amp;amp; Series\n- Horror Movies &amp;amp; Series\n- Movie News &amp;amp; Discussion\n- Reality TV\n- Romance Movies &amp;amp; Series\n- Sci-Fi Movies &amp;amp; Series\n- Superhero Movies &amp;amp; Series\n- TV News &amp;amp; Discussion\n\nRESOURCES\n\nAbout Reddit\n\nAdvertise\n\nReddit Pro\n\n      BETA\n\nHelp\n\nBlog\n\nCareers\n\nPress\n\nCommunities\n\nBest of Reddit\n\nTopics'''


import json


#读取 /Users/j4-ai/workspace/OCG/AI_search_content/2025-03-14-01-19-24.json 
# 然后展开
# 把里面的spanned_content 全部写入到tmp.md

the_dict = json.load(open('/Users/j4-ai/workspace/OCG/AI_search_content/2025-03-14-01-19-24.json'))
#展开
for subquestion,subquestion_dict in the_dict['subquestion'].items():
    for obj in subquestion_dict['AI_search_content_list']:
        title = obj['title'].replace('/','_')
        content = obj['content']
        spanned_content = obj['spanned_content']
        with open (f'span_example/{title}.md', 'w') as f:
            f.write(f'# Content\n{content}\n\n# Spanned Content\n{spanned_content}')
