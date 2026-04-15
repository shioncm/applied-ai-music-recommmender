# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

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

- Generated taste profile:

```python
user_prefs = {
    "favorite_genre": "rock",
    "favorite_mood": "intense",
    "target_energy": 0.85,
    "likes_acoustic": False,
}
```

- Finalized "Algorithm Recipe"

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

- Flowchart

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

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this


---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}  

```markdown
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> VibeFinder 1.0

---

## 2. Intended Use

- What is this system trying to do
- Who is it for

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

## 3. How It Works (Short Explanation)

Describe your scoring logic in plain language.

- What features of each song does it consider
- What information about the user does it use
- How does it turn those into a number

Try to avoid code in this section, treat it like an explanation to a non programmer.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`
- Did you add or remove any songs
- What kinds of genres or moods are represented
- Whose taste does this data mostly reflect

---

## 5. Strengths

Where does your recommender work well

You can think about:
- Situations where the top results "felt right"
- Particular user profiles it served well
- Simplicity or transparency benefits

---

## 6. Limitations and Bias

Where does your recommender struggle

Some prompts:
- Does it ignore some genres or moods
- Does it treat all users as if they have the same taste shape
- Is it biased toward high energy or one genre by default
- How could this be unfair if used in a real product

---

## 7. Evaluation

How did you check your system

Examples:
- You tried multiple user profiles and wrote down whether the results matched your expectations
- You compared your simulation to what a real app like Spotify or YouTube tends to recommend
- You wrote tests for your scoring logic

You do not need a numeric metric, but if you used one, explain what it measures.

---

## 8. Future Work

If you had more time, how would you improve this recommender

Examples:

- Add support for multiple users and "group vibe" recommendations
- Balance diversity of songs instead of always picking the closest match
- Use more features, like tempo ranges or lyric themes

---

## 9. Personal Reflection

A few sentences about what you learned:

- What surprised you about how your system behaved
- How did building this change how you think about real music recommenders
- Where do you think human judgment still matters, even if the model seems "smart"

