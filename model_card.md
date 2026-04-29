# 🎧 Model Card: Music Recommender Simulation

## 1. Song Seeker  

## 2. Intended Use  

- What kind of recommendations does it generate  

The recommender suggests the top five songs from an 18-song catalog. Recommendations are based on how closely each song matches the user's preferred genre, mood, energy level, and acoustic taste.

- What assumptions does it make about the user  

The recommender assumes each user has exactly one favorite genre, one favorite mood, and a specific energy target between 0 and 1. It also assumes they either like or dislike acoustic music, with no middle ground.

- Is this for real users or classroom exploration  

This is built for classroom exploration. It is a simulation, not a tool meant for real listeners.

- How has the system changed from the original prototype

The original system only accepted structured profiles. The current version adds a RAG pipeline: a natural language query is parsed into a structured profile by Gemini 2.5 Flash Lite, the original scorer retrieves the top five songs, and a second Gemini call generates a narrative explaining why each song fits. A confidence guardrail blocks results that score below 0.30.

---

## 3. How the Model Works  

- What features of each song are used (genre, energy, mood, etc.)  

Four features are used: genre, mood, energy, and acousticness. Genre and mood are checked for an exact match. Energy is a number from 0 to 1. Acousticness measures how acoustic-sounding the song is.

- What user preferences are considered  

The user provides a favorite genre, a favorite mood, a target energy level, and whether they prefer acoustic or non-acoustic music.

- How does the model turn those into a score  

Each feature that matches or is close to the user's preference adds points. Genre adds the most, then mood, then energy, then acousticness. The scores are added up and the top five songs are returned.

- What changes did you make from the starter logic  

The starter code just returned the first five songs in the file without any scoring. The scoring logic was added to make recommendations based on actual user preferences.

- What does the RAG layer add on top of the scorer

Two LLM calls wrap the scorer. The first is `parse_query`, which takes a natural language description and returns a structured profile in the format the scorer expects. The second is `narrate_recommendations`, which receives the retrieved songs and their scores and generates a conversational explanation. Neither call invents attributes or suggests songs outside the retrieved list.

---

## 4. Data  

- How many songs are in the catalog  

There are 18 songs. Each has a title, artist, genre, mood, energy level, tempo, valence, danceability, and acousticness score.

- What genres or moods are represented  

Genres include pop, lofi, rock, metal, jazz, blues, hip-hop, electronic, classical, reggae, and others. Moods include happy, chill, intense, sad, angry, melancholic, peaceful, and more. Most appear only once.

- Did you add or remove data  

Songs were added to the original starter CSV file during development. No songs were removed. The additions helped cover more genres and moods.

- Are there parts of musical taste missing in the dataset  

Most genres and moods have only one song each. Low-energy music like meditation is nearly absent.

---

## 5. Strengths   

- User types for which it gives reasonable results  

Lofi and pop fans get the best results because those genres have multiple catalog entries, ensuring a strong top result.

- Any patterns you think your scoring captures correctly  

The scoring correctly highly scores songs that match on multiple dimensions at once. A song with the right genre, right mood, and close energy will always beat one that only matches on one of those.

- Cases where the recommendations matched your intuition  

The Chill Lofi profile returned Library Rain and Midnight Coding at the top, which makes sense. Deep Intense Rock surfaced Storm Runner first, the only rock song, as expected.

---

## 6. Limitations and Bias 

- Features it does not consider  

Valence, danceability, and tempo are loaded for every song but never used in scoring.

- Genres or moods that are underrepresented  

13 of the 15 genres appear only once in the catalog, and most moods are equally sparse. 

- Cases where the system overfits to one preference  

Once genre is exhausted, the remaining slots are filled by whichever songs have the closest energy level. A rock fan and a reggae fan end up with nearly identical second-through-fifth recommendations.

- Ways the scoring might unintentionally favor some users  

The exact genre match penalizes users whose preferences do not align with the catalog's labels. A fan of metal is not recommended a rock song, while a lofi fan benefits from the three catalog entries.

- What is one weakness you discovered during your experiments 

The acoustic preference is a binary flag, so every user is treated as either an acoustic fan or a non-acoustic fan. The Acoustic Electronic edge case exposed this: the profile wanted electronic music but had the acoustic flag on, which penalized the best genre matches and pushed unrelated ambient songs up the list.

---

## 7. Evaluation    

- Which user profiles you tested  

Seven user profiles were tested. Four standard (Default Pop / Happy, High-Energy Pop, Chill Lofi, Deep Intense Rock) and three edge cases (Sad Bangers, Ghost Genre, Acoustic Electronic).

- What you looked for in the recommendations 

I looked for whether the top results matched each profile's stated genre and mood, and whether conflicting preferences returned irrelevant songs.

- What surprised you  

One thing that surprised me was how Gym Hero appeared at #2 for the happy pop user even though it is a workout anthem, not a feel-good track. The algorithm recipe rewards a genre match regardless of whether the mood also lines up.

- Any simple tests or comparisons you ran  

As a simple test, I compared Default Pop / Happy against High-Energy Pop. Switching the mood from happy to intense moved Gym Hero from #2 to #1. I also compared Sad Bangers against Ghost Genre, which are both edge cases. They broke the genre signal, but differently: one had a genre match that didn't satisfy the energy target; the other had no genre match at all.

---

## 8. Future Work   

- Additional features or preferences  

Valence, danceability, and tempo are already stored for every song but never scored. Adding them would let the system tell apart songs that are rhythmically different, even when genre and mood match.

- Better ways to explain recommendations  

Right now the explanation just lists which features added points. It would be more useful to also flag why a song ranked lower.

- Improving diversity among the top results  

The top five can include the same artist more than once if their songs score similarly. A simple rule capping each artist at one slot would make the results more varied.

- Handling more complex user tastes  

Right now each user has one favorite genre and one favorite mood. Letting users say they like more than one genre would better reflect how people actually listen to music.

---

## 9. Personal Reflection   

- What you learned about recommender systems  

I learned how music recommender system match users with songs. Learning about what features are commonly used for this matching was interesting.

- Something unexpected or interesting you discovered  

Small weight changes barely shifted the top result but completely reordered everything below it. This showed how sensitive ranking systems are.

- How this changed the way you think about music recommendation apps  

Real apps must score dozens of features to provide a personalized experience, and must consider many more factors.

---

## 10. AI Collaboration

- One instance where AI gave a helpful suggestion

One helpful suggestion was using the `response_schema` parameter in the Gemini API call for `parse_query`. Rather than prompting the model to return JSON and then manually parsing and validating it, the `response_schema` parameter accepts the Pydantic model directly and guarantees the output matches the schema. This removed the need for parsing errors.

- One instance where AI gave a flawed suggestion

One suggestion that was flawed was early in the design, AI recommended adding semantic embeddings for genre and mood matching to replace the binary string equality. That is a real limitation of the current system, but the proposed fix was far too complicated for an 18-song catalog. The complexity was not proportionate to the problem.
