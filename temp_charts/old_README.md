# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

This recommender scores songs from an 18-song catalog against a user profile with four attributes: genre, mood, energy level, and acoustic preference. Each song gets a weighted score and the top five results are returned. Seven test profiles were used to evaluate whether the system behaved as expected.

---

## How The System Works

- How do real-world recommendations work?

Real-world music recommendation platforms use a hybrid model. For new users, content-based filtering is used. As data accumulates, the model shifts toward collaborative filtering for discovery. For established users, a blended apporach of both collaborative and content-based filtering is used.

- What features does each `Song` use in your system
  - For example: genre, mood, energy, tempo

This sytem makes recommendations primarily with content-based filtering, using song attributes. The features used are as follows, ordered by weight:
1. `genre`: Most intuitive user preference. Seven distinct values across ten songs, strong differentiator.
2. `mood`: Context indicator, six distinct values across 10 songs. 
3. `energy`: Wide range (0.28 - 0.93), cleanly separates calm songs from intense ones.
4. `acousticness`: Wide range (0.05 - 0.92), cleanly separates acoustic songs from those that are not.
5. `tempo_bpm`: Adds nuance to `energy`. Good secondary signal.
6. `valence`: Correlated with `mood`. Separates emotionally positive from darker-toned songs. Good secondary signal.

- What information does your `UserProfile` store

The `UserProfile` stores the following:
1. favorite_genre: string value for the user's preferred genre
2. favorite_mood: string value for the user's preferred mood
3. target_energy_level: float value (0-1) for the user's desired energy level
4. likes_acousitc: boolean value for whether the user preferes acoustic over produced

- How does your `Recommender` compute a score for each song

A simple weighted score will be computed as follows:

`score = 0.35 * genre_match + 0.30 * mood_match + 0.20 * energy_similarity + 0.15 * acoustic_match`

where:

`genre_match: 1.0 if match, 0.0 if not`  
`mood_match: 1.0 if match, 0.0 if not`  
`energy_similarity: 1 - abs(user_energy - song_energy)`  
`acoustic_match: based on likes_acoustic vs acousticness`   

- How do you choose which songs to recommend

Songs to recommend are chosen based on the weighted score calculated for the song. For each song, the score will be calculated. These scored songs will then be ranked against each other.

### Generated taste profile:

```python
{
  "name": "Default Pop / Happy",
  "favorite_genre": "pop",
  "favorite_mood": "happy",
  "target_energy": 0.8,
  "likes_acoustic": False,
}
```

### Finalized "Algorithm Recipe"

```python
score(song, user) =
    0.35 * genre_match(song, user)
  + 0.30 * mood_match(song, user)
  + 0.20 * energy_similarity(song, user)
  + 0.15 * acoustic_match(song, user)
```

where:

```python
if song.genre == user.favorite_genre:
  genre_match = 1.0
else: 
  genre_match = 0.0

if song.mood  == user.favorite_mood:
  mood_match = 1.0
else: 
  mood_match = 0.0

energy_similarity = 1.0 - abs(song.energy - user.target_energy)

if user.likes_acoustic:
  acoustic_match = song.acousticness
if not user.likes_acoustic
  acoustic_match = 1.0 - song.acousticness
```

The following are potential biases to expect:
- Genre dominance: at 35%, a genre match outweighs every other signal. A same-genre may outscore songs that match other features heavily.
- String equality: genre and mood use string equality. However, this may mean adjacent values, such as "indie pop" and "pop," are evaluated as a complete mismatch.

### Flowchart (Mermaid.js)

```bash
flowchart TD
    A["User Preferences
    favorite_genre · favorite_mood
    target_energy · likes_acoustic"] --> D
    B["songs.csv"] --> C["Load all songs into list"]
    C --> D{More songs\nto score?}

    D -- Yes --> E["Take next song"]

    E --> F{Genre match?}
    F -- Yes --> G["+0.35"]
    F -- No  --> H["+0.00"]

    G --> I{Mood match?}
    H --> I
    I -- Yes --> J["+0.30"]
    I -- No  --> K["+0.00"]

    J --> L["+0.20 × (1.0 − |song.energy − target_energy|)"]
    K --> L

    L --> M{likes_acoustic?}
    M -- Yes --> N["+0.15 × song.acousticness"]
    M -- No  --> O["+0.15 × (1 − song.acousticness)"]

    N --> P["Sum → song score (0.0 – 1.0)"]
    O --> P

    P --> Q["Append (song, score) to results"]
    Q --> D

    D -- No --> R["Sort results by score ↓"]
    R --> S["Return top K songs"]
```

### CLI Verification

![phase3](./phase3_output.png)



---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 0.35 to 0.15

Decreasing the weight on genre allows high-energy songs from completely unrelated genres flood mid-rank slots. For instance, "Gym Hero" now ranks second in the "Deep Intense Rock" category.

- What happened when you changed the weight on energy from 0.20 to 0.40

Increasing the weight for energy adds nuance within a genre cluster. It improves accuracy for categories like "High Energy Pop"

- How did your system behave for different types of users

Profiles with popular genres like lofi and pop received the most relevant results because those genres had multiple catalog entries. A profile requesting a genre not in the catalog received results based entirely on mood and energy.

### Results of Stress Testing with Diverse Profiles

![phase_4_chill_lofi](./phase4_chill_lofi_output.png)
![phase_4_default_pop](./phase4_default_pop_output.png)
![phase_4_high_energy](./phase4_high_energy_output.png)
![phase_4_intense_rock](./phase4_intense_rock_output.png)
![phase_4_electronic](./phase4_electronic_output.png)
![phase4_ghost_genre](./phase4_ghost_genre_output.png)
![phase_4_sad_bangers](./phase4_sad_bangers_output.png)


---

## Limitations and Risks

Summarize some limitations of your recommender.

The catalog only has 18 songs, so most genres and moods appear just once. The system does not consider lyrics, tempo, or emotional nuance. Genre is matched as an exact string, so related genres like rock and metal are treated as completely different.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions

Recommenders turn data into predictions by assigning weights to features and computing how closely each item matches a user profile. This system shows that even a simple scoring algorithm can produce reasonable results, but the quality depends heavily on the catalog.

- about where bias or unfairness could show up in systems like this

Bias appears when the catalog does not represent all preferences equally. Users with rare genre or mood preferences get weaker results after the first match, while lofi fans benefit from three catalog entries.


---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}  

```markdown
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> TuneRecipe

---

## 2. Intended Use

- What is this system trying to do

The recommender suggests the top five songs from an 18-song catalog. Recommendations are based on how closely each song matches the user's preferred genre, mood, energy level, and acoustic taste.

- Who is it for

The recommender is primarily built for people interested in recommendation system implemntations, as this is built for classroom exploration. It is a simulation, not a tool meant for real listeners.

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

## 3. How It Works (Short Explanation)

Describe your scoring logic in plain language.

- What features of each song does it consider

Four features are used: genre, mood, energy, and acousticness. Genre and mood are checked for an exact match. Energy is a number from 0 to 1. Acousticness measures how acoustic-sounding the song is.

- What information about the user does it use

The user provides a favorite genre, a favorite mood, a target energy level, and whether they prefer acoustic or non-acoustic music.

- How does it turn those into a number

Each feature that matches or is close to the user's preference adds points. Genre adds the most, then mood, then energy, then acousticness. The scores are added up and the top five songs are returned.

Try to avoid code in this section, treat it like an explanation to a non programmer.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`

There are 18 songs. Each has a title, artist, genre, mood, energy level, tempo, valence, danceability, and acousticness score.

- Did you add or remove any songs

Songs were added to the original starter CSV file during development. No songs were removed. The additions helped cover more genres and moods.

- What kinds of genres or moods are represented

Genres include pop, lofi, rock, metal, jazz, blues, hip-hop, electronic, classical, reggae, and others. Moods include happy, chill, intense, sad, angry, melancholic, peaceful, and more. Most appear only once.

- Whose taste does this data mostly reflect

This recommender mostly reflects pop or lofi fans that prefer a happy or chill mood.

---

## 5. Strengths

Where does your recommender work well

- User types for which it gives reasonable results  

Lofi and pop fans get the best results because those genres have multiple catalog entries, ensuring a strong top result.

- Any patterns you think your scoring captures correctly  

The scoring correctly highly scores songs that match on multiple dimensions at once. A song with the right genre, right mood, and close energy will always beat one that only matches on one of those.

- Cases where the recommendations matched your intuition  

The Chill Lofi profile returned Library Rain and Midnight Coding at the top, which makes sense. Deep Intense Rock surfaced Storm Runner first, the only rock song, as expected.

---

## 6. Limitations and Bias

Where does your recommender struggle

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

How did you check your system

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

If you had more time, how would you improve this recommender

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

A few sentences about what you learned:

- What surprised you about how your system behaved

Small weight changes barely shifted the top result but completely reordered everything below it. This showed how sensitive ranking systems are.

- How did building this change how you think about real music recommenders

Real apps must score dozens of features to provide a personalized experience, and must consider many more factors. 

- Where do you think human judgment still matters, even if the model seems "smart"

- I think human judgement will still matter in the curation of songs, especially in music genres that are rare or unexplored.

---

## 10. Final Reflection

- What was your biggest learning moment during this project?

Evaluating which features I wanted to use in the scoring algorithm, and creating the final Algorithm Recipe.

- How did using AI tools help you, and when did you need to double-check them?

AI tools sped up score analysis. I had to double-check song rank numbers after changing weights, since earlier outputs reflected a different configuration.

- What surprised you about how simple algorithms can still "feel" like recommendations?

Even four features produced results that felt intuitive. The lofi rankings especially felt right despite the small catalog of songs.

- What would you try next if you extended this project?

I would add valence and tempo to the score and let users list more than one favorite genre. 