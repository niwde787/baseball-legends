<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Basketball Legends: The Pantheon</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #1A2238; /* Consistent Dark Blue */
        }
        .menu-button {
            transition: all 0.2s ease-in-out;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
            background-color: #4A5568;
            border: 1px solid #718096;
        }
        .menu-button:hover:not(:disabled) {
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
            background-color: #2D3748;
        }
        .action-button {
             background-color: #4299E1; /* Primary Blue */
        }
        .action-button:hover {
            background-color: #2B6CB0;
        }
        .player-slot {
            transition: all 0.2s ease-in-out;
            border: 2px dashed #4A5568;
            background-color: #2D3748;
        }
        .player-slot:hover {
            border-color: #63B3ED;
            background-color: #4A5568;
        }
        .player-slot.filled {
            border-style: solid;
            border-color: #4299E1;
            background-color: #1A2238;
        }
        #player-modal {
            background-color: rgba(0,0,0,0.8);
        }
        .logo-shape {
            clip-path: polygon(0 15%, 15% 0, 85% 0, 100% 15%, 100% 85%, 85% 100%, 15% 100%, 0 85%);
        }
    </style>
</head>
<body class="text-gray-200 antialiased">

    <div id="app-container" class="container mx-auto p-4 md:p-8 max-w-5xl relative">
        <!-- App content is rendered here by JavaScript -->
    </div>

    <script type="module">
        // --- DATA MODULE ---
        const players = {
            "kareem_abdul_jabbar": { name: "Kareem Abdul-Jabbar", pos: "C", tier: "GOAT", attributes: { inside_scoring: 100, mid_range: 88, three_point: 10, playmaking: 78, perimeter_defense: 60, interior_defense: 96, rebounding: 94, athleticism: 88, basketball_iq: 98 }, career_stats: { usg_pct: 28.5, fg_pct: 55.9 }, shot_tendencies: { inside: 80, mid: 20, three: 0 }, target_minutes: 38, traits: ["Unstoppable Scorer", "Rim Protector"], foul_tendency: 6, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=KAJ", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "wilt_chamberlain": { name: "Wilt Chamberlain", pos: "C", tier: "GOAT", attributes: { inside_scoring: 100, mid_range: 75, three_point: 5, playmaking: 70, perimeter_defense: 50, interior_defense: 95, rebounding: 100, athleticism: 100, basketball_iq: 85 }, career_stats: { usg_pct: 30.0, fg_pct: 54.0 }, shot_tendencies: { inside: 90, mid: 10, three: 0 }, target_minutes: 40, traits: ["Post Anchor", "Tireless Motor"], foul_tendency: 5, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=WC", era: "Pioneers Era (1940s-1960s)" },
            "michael_jordan": { name: "Michael Jordan", pos: "SG", tier: "GOAT", attributes: { inside_scoring: 98, mid_range: 100, three_point: 75, playmaking: 90, perimeter_defense: 98, interior_defense: 70, rebounding: 75, athleticism: 98, basketball_iq: 97 }, career_stats: { usg_pct: 33.3, fg_pct: 49.7 }, shot_tendencies: { inside: 45, mid: 50, three: 5 }, target_minutes: 38, traits: ["Clutch Performer", "Alpha Dog", "Unstoppable Scorer"], foul_tendency: 4, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=MJ", era: "Modern Era (1990s-2000s)" },
            "bill_russell": { name: "Bill Russell", pos: "C", tier: "GOAT", attributes: { inside_scoring: 75, mid_range: 50, three_point: 5, playmaking: 75, perimeter_defense: 70, interior_defense: 100, rebounding: 99, athleticism: 90, basketball_iq: 100 }, career_stats: { usg_pct: 16.6, fg_pct: 44.0 }, shot_tendencies: { inside: 95, mid: 5, three: 0 }, target_minutes: 36, traits: ["Rim Protector", "Alpha Dog"], foul_tendency: 7, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=BR", era: "Pioneers Era (1940s-1960s)" },
            "magic_johnson": { name: "Magic Johnson", pos: "PG", tier: "GOAT", attributes: { inside_scoring: 92, mid_range: 80, three_point: 70, playmaking: 100, perimeter_defense: 80, interior_defense: 60, rebounding: 80, athleticism: 88, basketball_iq: 99 }, career_stats: { usg_pct: 22.8, fg_pct: 52.0 }, shot_tendencies: { inside: 60, mid: 30, three: 10 }, target_minutes: 37, traits: ["Floor General", "Transition Threat"], foul_tendency: 4, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=MJ", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "larry_bird": { name: "Larry Bird", pos: "SF", tier: "GOAT", attributes: { inside_scoring: 88, mid_range: 96, three_point: 90, playmaking: 94, perimeter_defense: 80, interior_defense: 72, rebounding: 88, athleticism: 80, basketball_iq: 100 }, career_stats: { usg_pct: 26.5, fg_pct: 49.6 }, shot_tendencies: { inside: 35, mid: 45, three: 20 }, target_minutes: 38, traits: ["Clutch Performer", "Floor General"], foul_tendency: 5, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=LB", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "hakeem_olajuwon": { name: "Hakeem Olajuwon", pos: "C", tier: "Legend", attributes: { inside_scoring: 97, mid_range: 85, three_point: 20, playmaking: 70, perimeter_defense: 75, interior_defense: 99, rebounding: 93, athleticism: 92, basketball_iq: 95 }, career_stats: { usg_pct: 28.9, fg_pct: 51.2 }, shot_tendencies: { inside: 75, mid: 25, three: 0 }, target_minutes: 36, traits: ["Unstoppable Scorer", "Rim Protector"], foul_tendency: 8, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=HO", era: "Modern Era (1990s-2000s)" },
            "oscar_robertson": { name: "Oscar Robertson", pos: "PG", tier: "Legend", attributes: { inside_scoring: 90, mid_range: 92, three_point: 50, playmaking: 98, perimeter_defense: 85, interior_defense: 60, rebounding: 82, athleticism: 85, basketball_iq: 96 }, career_stats: { usg_pct: 26.0, fg_pct: 48.5 }, shot_tendencies: { inside: 50, mid: 50, three: 0 }, target_minutes: 38, traits: ["Floor General", "Tireless Motor"], foul_tendency: 5, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=OR", era: "Pioneers Era (1940s-1960s)" },
            "shaquille_oneal": { name: "Shaquille O'Neal", pos: "C", tier: "Legend", attributes: { inside_scoring: 100, mid_range: 25, three_point: 5, playmaking: 65, perimeter_defense: 30, interior_defense: 92, rebounding: 94, athleticism: 95, basketball_iq: 80 }, career_stats: { usg_pct: 29.5, fg_pct: 58.2 }, shot_tendencies: { inside: 99, mid: 1, three: 0 }, target_minutes: 35, traits: ["Post Anchor", "Rim Protector"], foul_tendency: 9, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=SO", era: "Modern Era (1990s-2000s)" },
            "jerry_west": { name: "Jerry West", pos: "SG", tier: "Legend", attributes: { inside_scoring: 85, mid_range: 95, three_point: 80, playmaking: 90, perimeter_defense: 92, interior_defense: 60, rebounding: 70, athleticism: 88, basketball_iq: 94 }, career_stats: { usg_pct: 30.0, fg_pct: 47.4 }, shot_tendencies: { inside: 40, mid: 60, three: 0 }, target_minutes: 37, traits: ["Clutch Performer", "Unstoppable Scorer"], foul_tendency: 5, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=JW", era: "Pioneers Era (1940s-1960s)" },
            "elgin_baylor": { name: "Elgin Baylor", pos: "SF", tier: "Legend", attributes: { inside_scoring: 96, mid_range: 90, three_point: 40, playmaking: 80, perimeter_defense: 78, interior_defense: 65, rebounding: 92, athleticism: 93, basketball_iq: 90 }, career_stats: { usg_pct: 29.0, fg_pct: 43.1 }, shot_tendencies: { inside: 60, mid: 40, three: 0 }, target_minutes: 36, traits: ["Unstoppable Scorer", "Tireless Motor"], foul_tendency: 6, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=EB", era: "Pioneers Era (1940s-1960s)" },
            "karl_malone": { name: "Karl Malone", pos: "PF", tier: "Legend", attributes: { inside_scoring: 95, mid_range: 88, three_point: 40, playmaking: 70, perimeter_defense: 78, interior_defense: 75, rebounding: 90, athleticism: 94, basketball_iq: 85 }, career_stats: { usg_pct: 28.7, fg_pct: 51.6 }, shot_tendencies: { inside: 60, mid: 40, three: 0 }, target_minutes: 37, traits: ["Post Anchor", "Transition Threat"], foul_tendency: 8, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=KM", era: "Modern Era (1990s-2000s)" },
            "moses_malone": { name: "Moses Malone", pos: "C", tier: "Legend", attributes: { inside_scoring: 94, mid_range: 70, three_point: 20, playmaking: 60, perimeter_defense: 60, interior_defense: 88, rebounding: 98, athleticism: 85, basketball_iq: 88 }, career_stats: { usg_pct: 26.1, fg_pct: 49.1 }, shot_tendencies: { inside: 85, mid: 15, three: 0 }, target_minutes: 34, traits: ["Post Anchor", "Tireless Motor"], foul_tendency: 7, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=MM", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "julius_erving": { name: "Julius Erving", pos: "SF", tier: "Legend", attributes: { inside_scoring: 97, mid_range: 80, three_point: 65, playmaking: 80, perimeter_defense: 85, interior_defense: 75, rebounding: 85, athleticism: 96, basketball_iq: 90 }, career_stats: { usg_pct: 28.8, fg_pct: 50.6 }, shot_tendencies: { inside: 70, mid: 25, three: 5 }, target_minutes: 36, traits: ["Transition Threat", "Unstoppable Scorer"], foul_tendency: 6, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=JE", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "charles_barkley": { name: "Charles Barkley", pos: "PF", tier: "Legend", attributes: { inside_scoring: 92, mid_range: 80, three_point: 70, playmaking: 75, perimeter_defense: 70, interior_defense: 65, rebounding: 95, athleticism: 90, basketball_iq: 87 }, career_stats: { usg_pct: 26.6, fg_pct: 54.1 }, shot_tendencies: { inside: 65, mid: 25, three: 10 }, target_minutes: 35, traits: ["Tireless Motor", "Post Anchor"], foul_tendency: 8, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=CB", era: "Modern Era (1990s-2000s)" },
            "scottie_pippen": { name: "Scottie Pippen", pos: "SF", tier: "Legend", attributes: { inside_scoring: 85, mid_range: 82, three_point: 75, playmaking: 88, perimeter_defense: 100, interior_defense: 80, rebounding: 80, athleticism: 92, basketball_iq: 93 }, career_stats: { usg_pct: 21.0, fg_pct: 47.3 }, shot_tendencies: { inside: 45, mid: 35, three: 20 }, target_minutes: 35, traits: ["Lockdown Defender", "Transition Threat"], foul_tendency: 4, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=SP", era: "Modern Era (1990s-2000s)" },
            "john_stockton": { name: "John Stockton", pos: "PG", tier: "Legend", attributes: { inside_scoring: 75, mid_range: 85, three_point: 82, playmaking: 99, perimeter_defense: 94, interior_defense: 40, rebounding: 50, athleticism: 80, basketball_iq: 97 }, career_stats: { usg_pct: 18.0, fg_pct: 51.5 }, shot_tendencies: { inside: 40, mid: 40, three: 20 }, target_minutes: 34, traits: ["Floor General", "Lockdown Defender"], foul_tendency: 4, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=JS", era: "Modern Era (1990s-2000s)" },
            "isiah_thomas": { name: "Isiah Thomas", pos: "PG", tier: "Legend", attributes: { inside_scoring: 88, mid_range: 86, three_point: 70, playmaking: 95, perimeter_defense: 88, interior_defense: 45, rebounding: 60, athleticism: 91, basketball_iq: 92 }, career_stats: { usg_pct: 26.2, fg_pct: 45.2 }, shot_tendencies: { inside: 50, mid: 40, three: 10 }, target_minutes: 36, traits: ["Ankle Breaker", "Floor General"], foul_tendency: 6, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=IT", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "patrick_ewing": { name: "Patrick Ewing", pos: "C", tier: "Legend", attributes: { inside_scoring: 90, mid_range: 92, three_point: 20, playmaking: 60, perimeter_defense: 50, interior_defense: 94, rebounding: 91, athleticism: 86, basketball_iq: 84 }, career_stats: { usg_pct: 29.0, fg_pct: 50.4 }, shot_tendencies: { inside: 50, mid: 50, three: 0 }, target_minutes: 35, traits: ["Rim Protector", "Unstoppable Scorer"], foul_tendency: 7, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=PE", era: "Modern Era (1990s-2000s)" },
            "david_robinson": { name: "David Robinson", pos: "C", tier: "Legend", attributes: { inside_scoring: 93, mid_range: 84, three_point: 50, playmaking: 70, perimeter_defense: 70, interior_defense: 95, rebounding: 92, athleticism: 95, basketball_iq: 91 }, career_stats: { usg_pct: 28.5, fg_pct: 51.8 }, shot_tendencies: { inside: 65, mid: 30, three: 5 }, target_minutes: 34, traits: ["Rim Protector", "Transition Threat"], foul_tendency: 6, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=DR", era: "Modern Era (1990s-2000s)" },
            "clyde_drexler": { name: "Clyde Drexler", pos: "SG", tier: "Legend", attributes: { inside_scoring: 90, mid_range: 80, three_point: 78, playmaking: 85, perimeter_defense: 84, interior_defense: 60, rebounding: 78, athleticism: 94, basketball_iq: 88 }, career_stats: { usg_pct: 26.1, fg_pct: 47.2 }, shot_tendencies: { inside: 50, mid: 30, three: 20 }, target_minutes: 34, traits: ["Transition Threat", "Ankle Breaker"], foul_tendency: 5, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=CD", era: "Modern Era (1990s-2000s)" },
            "george_gervin": { name: "George Gervin", pos: "SG", tier: "Legend", attributes: { inside_scoring: 94, mid_range: 96, three_point: 60, playmaking: 70, perimeter_defense: 70, interior_defense: 50, rebounding: 65, athleticism: 87, basketball_iq: 85 }, career_stats: { usg_pct: 32.8, fg_pct: 51.1 }, shot_tendencies: { inside: 50, mid: 50, three: 0 }, target_minutes: 33, traits: ["Unstoppable Scorer", "Heat Check"], foul_tendency: 7, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=GG", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "john_havlicek": { name: "John Havlicek", pos: "SF", tier: "Legend", attributes: { inside_scoring: 86, mid_range: 88, three_point: 50, playmaking: 85, perimeter_defense: 90, interior_defense: 65, rebounding: 78, athleticism: 88, basketball_iq: 93 }, career_stats: { usg_pct: 25.0, fg_pct: 43.9 }, shot_tendencies: { inside: 50, mid: 50, three: 0 }, target_minutes: 36, traits: ["Tireless Motor", "Clutch Performer"], foul_tendency: 4, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=JH", era: "Pioneers Era (1940s-1960s)" },
            "rick_barry": { name: "Rick Barry", pos: "SF", tier: "Legend", attributes: { inside_scoring: 84, mid_range: 90, three_point: 80, playmaking: 86, perimeter_defense: 82, interior_defense: 60, rebounding: 75, athleticism: 84, basketball_iq: 90 }, career_stats: { usg_pct: 27.5, fg_pct: 44.9 }, shot_tendencies: { inside: 40, mid: 40, three: 20 }, target_minutes: 35, traits: ["Unstoppable Scorer", "Floor General"], foul_tendency: 6, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=RB", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "bob_pettit": { name: "Bob Pettit", pos: "PF", tier: "Legend", attributes: { inside_scoring: 92, mid_range: 85, three_point: 30, playmaking: 70, perimeter_defense: 70, interior_defense: 75, rebounding: 96, athleticism: 85, basketball_iq: 88 }, career_stats: { usg_pct: 28.0, fg_pct: 43.6 }, shot_tendencies: { inside: 60, mid: 40, three: 0 }, target_minutes: 36, traits: ["Tireless Motor", "Post Anchor"], foul_tendency: 7, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=BP", era: "Pioneers Era (1940s-1960s)" },
            "walt_frazier": { name: "Walt Frazier", pos: "PG", tier: "All-Star", attributes: { inside_scoring: 80, mid_range: 88, three_point: 40, playmaking: 88, perimeter_defense: 97, interior_defense: 50, rebounding: 70, athleticism: 86, basketball_iq: 91 }, career_stats: { usg_pct: 24.0, fg_pct: 49.0 }, shot_tendencies: { inside: 40, mid: 60, three: 0 }, target_minutes: 34, traits: ["Lockdown Defender", "Floor General"], foul_tendency: 4, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=WF", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "kevin_mchale": { name: "Kevin McHale", pos: "PF", tier: "All-Star", attributes: { inside_scoring: 96, mid_range: 75, three_point: 30, playmaking: 65, perimeter_defense: 60, interior_defense: 90, rebounding: 85, athleticism: 80, basketball_iq: 89 }, career_stats: { usg_pct: 24.1, fg_pct: 55.4 }, shot_tendencies: { inside: 80, mid: 20, three: 0 }, target_minutes: 31, traits: ["Post Anchor", "Unstoppable Scorer"], foul_tendency: 7, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=KM", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "dolph_schayes": { name: "Dolph Schayes", pos: "PF", tier: "All-Star", attributes: { inside_scoring: 88, mid_range: 84, three_point: 20, playmaking: 70, perimeter_defense: 65, interior_defense: 70, rebounding: 93, athleticism: 80, basketball_iq: 86 }, career_stats: { usg_pct: 25.0, fg_pct: 38.0 }, shot_tendencies: { inside: 70, mid: 30, three: 0 }, target_minutes: 32, traits: ["Post Anchor", "Tireless Motor"], foul_tendency: 8, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=DS", era: "Pioneers Era (1940s-1960s)" },
            "elvin_hayes": { name: "Elvin Hayes", pos: "PF", tier: "All-Star", attributes: { inside_scoring: 90, mid_range: 88, three_point: 20, playmaking: 60, perimeter_defense: 60, interior_defense: 85, rebounding: 94, athleticism: 84, basketball_iq: 82 }, career_stats: { usg_pct: 27.2, fg_pct: 45.2 }, shot_tendencies: { inside: 50, mid: 50, three: 0 }, target_minutes: 34, traits: ["Unstoppable Scorer", "Rim Protector"], foul_tendency: 7, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=EH", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "dave_cowens": { name: "Dave Cowens", pos: "C", tier: "All-Star", attributes: { inside_scoring: 82, mid_range: 80, three_point: 20, playmaking: 75, perimeter_defense: 70, interior_defense: 80, rebounding: 92, athleticism: 88, basketball_iq: 88 }, career_stats: { usg_pct: 22.0, fg_pct: 46.0 }, shot_tendencies: { inside: 60, mid: 40, three: 0 }, target_minutes: 33, traits: ["Tireless Motor", "Transition Threat"], foul_tendency: 9, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=DC", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "wes_unseld": { name: "Wes Unseld", pos: "C", tier: "All-Star", attributes: { inside_scoring: 80, mid_range: 75, three_point: 10, playmaking: 80, perimeter_defense: 60, interior_defense: 85, rebounding: 95, athleticism: 80, basketball_iq: 90 }, career_stats: { usg_pct: 14.0, fg_pct: 50.9 }, shot_tendencies: { inside: 80, mid: 20, three: 0 }, target_minutes: 30, traits: ["Post Anchor", "Floor General"], foul_tendency: 6, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=WU", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "robert_parish": { name: "Robert Parish", pos: "C", tier: "All-Star", attributes: { inside_scoring: 88, mid_range: 86, three_point: 10, playmaking: 60, perimeter_defense: 50, interior_defense: 89, rebounding: 88, athleticism: 78, basketball_iq: 85 }, career_stats: { usg_pct: 19.8, fg_pct: 53.7 }, shot_tendencies: { inside: 60, mid: 40, three: 0 }, target_minutes: 28, traits: ["Rim Protector", "Post Anchor"], foul_tendency: 6, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=RP", era: "Modern Era (1990s-2000s)" },
            "bob_cousy": { name: "Bob Cousy", pos: "PG", tier: "All-Star", attributes: { inside_scoring: 78, mid_range: 80, three_point: 30, playmaking: 97, perimeter_defense: 75, interior_defense: 40, rebounding: 60, athleticism: 82, basketball_iq: 94 }, career_stats: { usg_pct: 26.0, fg_pct: 37.5 }, shot_tendencies: { inside: 50, mid: 50, three: 0 }, target_minutes: 32, traits: ["Floor General", "Ankle Breaker"], foul_tendency: 5, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=BC", era: "Pioneers Era (1940s-1960s)" },
            "james_worthy": { name: "James Worthy", pos: "SF", tier: "All-Star", attributes: { inside_scoring: 92, mid_range: 85, three_point: 50, playmaking: 75, perimeter_defense: 75, interior_defense: 60, rebounding: 70, athleticism: 90, basketball_iq: 86 }, career_stats: { usg_pct: 22.5, fg_pct: 52.1 }, shot_tendencies: { inside: 60, mid: 35, three: 5 }, target_minutes: 32, traits: ["Transition Threat", "Clutch Performer"], foul_tendency: 5, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=JW", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "nate_archibald": { name: "Nate Archibald", pos: "PG", tier: "All-Star", attributes: { inside_scoring: 88, mid_range: 82, three_point: 50, playmaking: 94, perimeter_defense: 80, interior_defense: 40, rebounding: 50, athleticism: 90, basketball_iq: 88 }, career_stats: { usg_pct: 25.0, fg_pct: 46.7 }, shot_tendencies: { inside: 60, mid: 35, three: 5 }, target_minutes: 33, traits: ["Floor General", "Ankle Breaker"], foul_tendency: 4, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=NA", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "bill_walton": { name: "Bill Walton", pos: "C", tier: "All-Star", attributes: { inside_scoring: 85, mid_range: 75, three_point: 20, playmaking: 88, perimeter_defense: 65, interior_defense: 92, rebounding: 93, athleticism: 82, basketball_iq: 95 }, career_stats: { usg_pct: 20.0, fg_pct: 52.1 }, shot_tendencies: { inside: 70, mid: 30, three: 0 }, target_minutes: 30, traits: ["Floor General", "Rim Protector"], foul_tendency: 7, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=BW", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "sam_jones": { name: "Sam Jones", pos: "SG", tier: "All-Star", attributes: { inside_scoring: 82, mid_range: 90, three_point: 40, playmaking: 70, perimeter_defense: 80, interior_defense: 50, rebounding: 65, athleticism: 84, basketball_iq: 88 }, career_stats: { usg_pct: 24.0, fg_pct: 45.6 }, shot_tendencies: { inside: 40, mid: 60, three: 0 }, target_minutes: 32, traits: ["Clutch Performer", "Unstoppable Scorer"], foul_tendency: 5, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=SJ", era: "Pioneers Era (1940s-1960s)" },
            "george_mikan": { name: "George Mikan", pos: "C", tier: "All-Star", attributes: { inside_scoring: 95, mid_range: 70, three_point: 5, playmaking: 65, perimeter_defense: 40, interior_defense: 88, rebounding: 90, athleticism: 70, basketball_iq: 85 }, career_stats: { usg_pct: 30.0, fg_pct: 40.4 }, shot_tendencies: { inside: 90, mid: 10, three: 0 }, target_minutes: 34, traits: ["Post Anchor", "Rim Protector"], foul_tendency: 9, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=GM", era: "Pioneers Era (1940s-1960s)" },
            "pete_maravich": { name: "Pete Maravich", pos: "SG", tier: "All-Star", attributes: { inside_scoring: 85, mid_range: 88, three_point: 75, playmaking: 92, perimeter_defense: 70, interior_defense: 40, rebounding: 60, athleticism: 85, basketball_iq: 89 }, career_stats: { usg_pct: 30.5, fg_pct: 44.1 }, shot_tendencies: { inside: 40, mid: 40, three: 20 }, target_minutes: 34, traits: ["Ankle Breaker", "Heat Check"], foul_tendency: 5, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=PM", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "dave_debusschere": { name: "Dave DeBusschere", pos: "PF", tier: "All-Star", attributes: { inside_scoring: 80, mid_range: 82, three_point: 30, playmaking: 70, perimeter_defense: 85, interior_defense: 80, rebounding: 90, athleticism: 82, basketball_iq: 88 }, career_stats: { usg_pct: 20.0, fg_pct: 43.2 }, shot_tendencies: { inside: 50, mid: 50, three: 0 }, target_minutes: 32, traits: ["Lockdown Defender", "Tireless Motor"], foul_tendency: 6, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=DD", era: "Pioneers Era (1940s-1960s)" },
            "jerry_lucas": { name: "Jerry Lucas", pos: "PF", tier: "All-Star", attributes: { inside_scoring: 82, mid_range: 88, three_point: 20, playmaking: 75, perimeter_defense: 70, interior_defense: 75, rebounding: 94, athleticism: 80, basketball_iq: 90 }, career_stats: { usg_pct: 20.0, fg_pct: 49.9 }, shot_tendencies: { inside: 50, mid: 50, three: 0 }, target_minutes: 31, traits: ["Post Anchor", "Floor General"], foul_tendency: 5, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=JL", era: "Pioneers Era (1940s-1960s)" },
            "earl_monroe": { name: "Earl Monroe", pos: "SG", tier: "All-Star", attributes: { inside_scoring: 88, mid_range: 86, three_point: 40, playmaking: 84, perimeter_defense: 75, interior_defense: 40, rebounding: 55, athleticism: 87, basketball_iq: 88 }, career_stats: { usg_pct: 25.5, fg_pct: 46.4 }, shot_tendencies: { inside: 60, mid: 40, three: 0 }, target_minutes: 32, traits: ["Ankle Breaker", "Unstoppable Scorer"], foul_tendency: 4, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=EM", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "bill_sharman": { name: "Bill Sharman", pos: "SG", tier: "All-Star", attributes: { inside_scoring: 75, mid_range: 94, three_point: 30, playmaking: 78, perimeter_defense: 84, interior_defense: 40, rebounding: 60, athleticism: 80, basketball_iq: 87 }, career_stats: { usg_pct: 24.0, fg_pct: 42.6 }, shot_tendencies: { inside: 40, mid: 60, three: 0 }, target_minutes: 32, traits: ["Heat Check", "Clutch Performer"], foul_tendency: 6, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=BS", era: "Pioneers Era (1940s-1960s)" },
            "lenny_wilkens": { name: "Lenny Wilkens", pos: "PG", tier: "All-Star", attributes: { inside_scoring: 80, mid_range: 85, three_point: 40, playmaking: 90, perimeter_defense: 82, interior_defense: 40, rebounding: 65, athleticism: 83, basketball_iq: 92 }, career_stats: { usg_pct: 22.0, fg_pct: 43.2 }, shot_tendencies: { inside: 50, mid: 50, three: 0 }, target_minutes: 33, traits: ["Floor General", "Lockdown Defender"], foul_tendency: 4, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=LW", era: "Pioneers Era (1940s-1960s)" },
            "dave_bing": { name: "Dave Bing", pos: "SG", tier: "All-Star", attributes: { inside_scoring: 86, mid_range: 87, three_point: 50, playmaking: 85, perimeter_defense: 78, interior_defense: 45, rebounding: 60, athleticism: 86, basketball_iq: 85 }, career_stats: { usg_pct: 26.0, fg_pct: 44.1 }, shot_tendencies: { inside: 50, mid: 50, three: 0 }, target_minutes: 33, traits: ["Unstoppable Scorer", "Transition Threat"], foul_tendency: 5, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=DB", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "hal_greer": { name: "Hal Greer", pos: "SG", tier: "All-Star", attributes: { inside_scoring: 84, mid_range: 90, three_point: 30, playmaking: 80, perimeter_defense: 78, interior_defense: 45, rebounding: 68, athleticism: 83, basketball_iq: 86 }, career_stats: { usg_pct: 24.0, fg_pct: 45.2 }, shot_tendencies: { inside: 40, mid: 60, three: 0 }, target_minutes: 32, traits: ["Heat Check", "Clutch Performer"], foul_tendency: 6, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=HG", era: "Pioneers Era (1940s-1960s)" },
            "paul_arizin": { name: "Paul Arizin", pos: "SF", tier: "All-Star", attributes: { inside_scoring: 88, mid_range: 91, three_point: 20, playmaking: 65, perimeter_defense: 70, interior_defense: 60, rebounding: 85, athleticism: 82, basketball_iq: 84 }, career_stats: { usg_pct: 28.0, fg_pct: 42.1 }, shot_tendencies: { inside: 50, mid: 50, three: 0 }, target_minutes: 31, traits: ["Unstoppable Scorer", "Tireless Motor"], foul_tendency: 7, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=PA", era: "Pioneers Era (1940s-1960s)" },
            "billy_cunningham": { name: "Billy Cunningham", pos: "SF", tier: "All-Star", attributes: { inside_scoring: 87, mid_range: 80, three_point: 30, playmaking: 78, perimeter_defense: 75, interior_defense: 65, rebounding: 88, athleticism: 85, basketball_iq: 87 }, career_stats: { usg_pct: 27.0, fg_pct: 44.6 }, shot_tendencies: { inside: 60, mid: 40, three: 0 }, target_minutes: 30, traits: ["Tireless Motor", "Transition Threat"], foul_tendency: 7, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=BC", era: "Showtime & Three-Point Era (1970s-1980s)" },
            "nate_thurmond": { name: "Nate Thurmond", pos: "C", tier: "All-Star", attributes: { inside_scoring: 80, mid_range: 70, three_point: 10, playmaking: 65, perimeter_defense: 60, interior_defense: 93, rebounding: 96, athleticism: 84, basketball_iq: 85 }, career_stats: { usg_pct: 18.0, fg_pct: 42.1 }, shot_tendencies: { inside: 70, mid: 30, three: 0 }, target_minutes: 30, traits: ["Rim Protector", "Post Anchor"], foul_tendency: 7, img_url: "https://placehold.co/64x64/FBBF24/1A2238?text=NT", era: "Pioneers Era (1940s-1960s)" }
        };

        const App = {
            rosters: {
                team1: { starters: {}, bench: {} },
                team2: { starters: {}, bench: {} }
            },
            selectedPlayers: new Set(),
            activeSlot: null,
            series: null,

            init() {
                this.renderHome();
                document.getElementById('app-container').addEventListener('click', (e) => {
                    if (e.target.classList.contains('view-box-score-btn')) {
                        if (this.series) {
                            this.series.viewBoxScore(e.target.dataset.gameIndex);
                        }
                    }
                });
            },

            renderHome() {
                document.getElementById('app-container').innerHTML = `
                    <div class="text-center pt-8 md:pt-16">
                         <div class="logo-shape bg-orange-500 w-48 h-48 mx-auto flex items-center justify-center p-4 shadow-lg mb-4">
                            <div class="text-center">
                                <div class="font-black text-3xl text-gray-900 tracking-tighter leading-none">BASKETBALL</div>
                                <div class="font-black text-3xl text-gray-900 tracking-tighter leading-none">LEGENDS</div>
                            </div>
                        </div>
                        <h1 class="text-3xl font-bold text-gray-200">Simulate your dream basketball matchups.</h1>
                        <div class="mt-12 space-y-6">
                            <div class="flex flex-col md:flex-row justify-center items-center gap-6">
                                <button id="goto-single-game-btn" class="menu-button text-white font-bold py-4 px-10 rounded-lg text-2xl w-64">Single Game</button>
                                <button id="goto-series-btn" class="menu-button text-white font-bold py-4 px-10 rounded-lg text-2xl w-64">Series</button>
                            </div>
                        </div>
                    </div>
                `;
                document.getElementById('goto-single-game-btn').addEventListener('click', () => this.renderRosterSetup(false));
                document.getElementById('goto-series-btn').addEventListener('click', () => this.renderRosterSetup(true));
            },
            
            addBackButton(handler) {
                const backButton = document.createElement('button');
                backButton.innerHTML = `&larr;`;
                backButton.className = 'absolute top-4 left-4 bg-gray-700 hover:bg-gray-600 rounded-full w-10 h-10 flex items-center justify-center text-2xl transition';
                backButton.onclick = handler;
                document.getElementById('app-container').prepend(backButton);
            },

            renderRosterSetup(isSeries) {
                this.rosters = { team1: { starters: {}, bench: {} }, team2: { starters: {}, bench: {} } };
                this.selectedPlayers.clear();
                const positions = ["PG", "SG", "SF", "PF", "C"];
                const title = isSeries ? 'Build Teams for a 7-Game Series' : 'Build Teams for a Single Game';
                const buttonText = isSeries ? 'Start Series' : 'Start Game';

                const teamTemplate = (teamNum, teamName) => `
                    <div class="space-y-4">
                        <div class="flex justify-between items-center">
                            <input type="text" id="team${teamNum}-name" class="bg-gray-900 text-2xl font-bold text-amber-300 border-none focus:ring-0" value="${teamName}">
                            <button class="menu-button text-sm py-2 px-4 rounded-lg" data-team-num="${teamNum}" id="randomize-team-${teamNum}-btn">Randomize</button>
                        </div>
                        ${['starters', 'bench'].map(type => `
                            <div>
                                <h4 class="text-lg font-semibold mb-2 border-b border-gray-600 pb-1 capitalize">${type}</h4>
                                <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                                    ${positions.map(pos => `
                                        <button class="player-slot h-24 rounded-lg flex flex-col items-center justify-center p-2" 
                                                data-team="team${teamNum}" data-type="${type}" data-pos="${pos}">
                                            <span class="font-bold text-gray-400">${pos}</span>
                                            <span class="text-sm text-gray-500 mt-1">+ Add Player</span>
                                        </button>
                                    `).join('')}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;

                document.getElementById('app-container').innerHTML = `
                    <header class="text-center mb-8">
                        <h1 class="text-4xl md:text-5xl font-bold text-amber-400">${title}</h1>
                    </header>
                    <div class="bg-gray-800 p-6 rounded-xl shadow-lg space-y-8">
                        ${teamTemplate(1, 'Team 1')}
                        <hr class="border-gray-600"/>
                        ${teamTemplate(2, 'Team 2')}
                    </div>
                    <div class="text-center mt-6">
                        <button id="start-simulation-btn" class="action-button menu-button font-bold py-3 px-8 rounded-lg text-xl">${buttonText}</button>
                    </div>
                    <div id="player-modal" class="hidden fixed inset-0 z-50 flex items-center justify-center p-4">
                        <div class="bg-gray-800 rounded-lg shadow-2xl max-w-md w-full max-h-[80vh] overflow-y-auto">
                            <div class="p-4 border-b border-gray-700 sticky top-0 bg-gray-800 z-10">
                                <h3 id="modal-title" class="text-xl font-bold">Select a Player</h3>
                                <input type="text" id="player-search" class="w-full p-2 mt-2 bg-gray-700 rounded-md" placeholder="Search by name...">
                                <div id="modal-filters" class="flex gap-2 mt-2"></div>
                            </div>
                            <div id="modal-player-list" class="p-4 grid grid-cols-1 sm:grid-cols-2 gap-2"></div>
                             <div class="p-4 border-t border-gray-700 sticky bottom-0 bg-gray-800">
                                <button id="close-modal-btn" class="w-full bg-red-600 hover:bg-red-700 p-2 rounded-lg">Cancel</button>
                            </div>
                        </div>
                    </div>
                `;
                this.addBackButton(() => this.renderHome());
                document.querySelectorAll('.player-slot').forEach(slot => slot.addEventListener('click', () => this.openPlayerModal(slot)));
                document.getElementById('close-modal-btn').addEventListener('click', () => this.closePlayerModal());
                document.getElementById('start-simulation-btn').addEventListener('click', () => this.startSimulation(isSeries));
                document.getElementById('randomize-team-1-btn').addEventListener('click', () => this.randomizeTeam(1));
                document.getElementById('randomize-team-2-btn').addEventListener('click', () => this.randomizeTeam(2));
            },

            openPlayerModal(slot) {
                this.activeSlot = slot;
                const { pos } = slot.dataset;
                document.getElementById('modal-title').textContent = `Select a ${pos}`;
                
                const searchInput = document.getElementById('player-search');
                searchInput.value = '';
                searchInput.onkeyup = () => this.filterModalPlayers();

                const filters = document.getElementById('modal-filters');
                filters.innerHTML = `
                    <button data-filter="All" class="modal-filter-btn bg-amber-500 p-2 rounded-md text-sm">All</button>
                    <button data-filter="GOAT" class="modal-filter-btn bg-gray-600 p-2 rounded-md text-sm">GOAT</button>
                    <button data-filter="Legend" class="modal-filter-btn bg-gray-600 p-2 rounded-md text-sm">Legend</button>
                    <button data-filter="All-Star" class="modal-filter-btn bg-gray-600 p-2 rounded-md text-sm">All-Star</button>
                `;
                document.querySelectorAll('.modal-filter-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        document.querySelectorAll('.modal-filter-btn').forEach(b => b.classList.replace('bg-amber-500', 'bg-gray-600'));
                        e.target.classList.replace('bg-gray-600', 'bg-amber-500');
                        this.filterModalPlayers();
                    });
                });

                this.filterModalPlayers();
                document.getElementById('player-modal').classList.remove('hidden');
            },

            filterModalPlayers() {
                const { pos } = this.activeSlot.dataset;
                const list = document.getElementById('modal-player-list');
                list.innerHTML = '';
                
                const searchTerm = document.getElementById('player-search').value.toLowerCase();
                const activeFilter = document.querySelector('.modal-filter-btn[data-filter].bg-amber-500').dataset.filter;

                const filtered = Object.entries(players).filter(([key, p]) => {
                    const posMatch = p.pos === pos;
                    const nameMatch = p.name.toLowerCase().includes(searchTerm);
                    const tierMatch = activeFilter === 'All' || p.tier === activeFilter;
                    return posMatch && nameMatch && tierMatch;
                });
                
                filtered.forEach(([key, p]) => {
                    const isSelected = this.selectedPlayers.has(key);
                    const btn = document.createElement('button');
                    btn.className = `p-3 rounded-lg text-left ${isSelected ? 'bg-gray-600 text-gray-400 cursor-not-allowed' : 'bg-gray-700 hover:bg-amber-600'}`;
                    btn.innerHTML = `<div class="flex items-center"><img src="${p.img_url}" class="w-8 h-8 rounded-full mr-3"><div class="flex-1"><div>${p.name}</div><div class="text-xs text-gray-400">${p.tier}</div></div></div>`;
                    btn.dataset.key = key;
                    btn.disabled = isSelected;
                    btn.addEventListener('click', () => this.selectPlayer(key));
                    list.appendChild(btn);
                });
            },

            closePlayerModal() {
                document.getElementById('player-modal').classList.add('hidden');
                this.activeSlot = null;
            },

            selectPlayer(playerKey, slot) {
                const targetSlot = slot || this.activeSlot;
                const { team, type, pos } = targetSlot.dataset;
                const oldPlayerKey = this.rosters[team][type][pos];
                if (oldPlayerKey) {
                    this.selectedPlayers.delete(oldPlayerKey);
                }
                this.rosters[team][type][pos] = playerKey;
                this.selectedPlayers.add(playerKey);
                
                targetSlot.innerHTML = `<img src="${players[playerKey].img_url}" class="w-12 h-12 rounded-full mx-auto mb-1"><span class="font-bold text-white text-xs">${players[playerKey].name}</span><span class="text-xs text-gray-400">${pos}</span>`;
                targetSlot.classList.add('filled');
                
                if(!slot) this.closePlayerModal();
            },

            randomizeTeam(teamNum) {
                const team = `team${teamNum}`;
                const positions = ["PG", "SG", "SF", "PF", "C"];
                
                ['starters', 'bench'].forEach(type => {
                    positions.forEach(pos => {
                        const oldPlayerKey = this.rosters[team][type][pos];
                        if (oldPlayerKey) {
                            this.selectedPlayers.delete(oldPlayerKey);
                        }
                        this.rosters[team][type][pos] = null;
                    });
                });

                const availablePlayersByPos = { PG: [], SG: [], SF: [], PF: [], C: [] };
                Object.entries(players).forEach(([key, player]) => {
                    if (!this.selectedPlayers.has(key)) {
                        availablePlayersByPos[player.pos].push(key);
                    }
                });

                ['starters', 'bench'].forEach(type => {
                    positions.forEach(pos => {
                        if (availablePlayersByPos[pos].length > 0) {
                            const randomIndex = Math.floor(Math.random() * availablePlayersByPos[pos].length);
                            const playerKey = availablePlayersByPos[pos].splice(randomIndex, 1)[0];
                            const slot = document.querySelector(`[data-team="${team}"][data-type="${type}"][data-pos="${pos}"]`);
                            this.selectPlayer(playerKey, slot);
                        }
                    });
                });
            },

            startSimulation(isSeries) {
                if (this.selectedPlayers.size < 20) {
                    alert("Please fill all 20 roster spots before starting.");
                    return;
                }
                
                const buildRosterArrays = (rosterObj) => ({
                    starters: Object.values(rosterObj.starters).map(key => JSON.parse(JSON.stringify(players[key]))),
                    bench: Object.values(rosterObj.bench).map(key => JSON.parse(JSON.stringify(players[key])))
                });
                
                const team1Name = document.getElementById('team1-name').value || "Team 1";
                const team2Name = document.getElementById('team2-name').value || "Team 2";

                if (isSeries) {
                    this.series = new Series(buildRosterArrays(this.rosters.team1), buildRosterArrays(this.rosters.team2), team1Name, team2Name);
                    this.series.renderSeriesScreen();
                } else {
                    const team1 = { name: team1Name, roster: buildRosterArrays(this.rosters.team1) };
                    const team2 = { name: team2Name, roster: buildRosterArrays(this.rosters.team2) };
                    const game = new SeriesGame(team1, team2, null);
                    game.renderGameScreen();
                }
            }
        };

        class Series {
            constructor(team1Roster, team2Roster, team1Name, team2Name) {
                this.team1 = { name: team1Name, roster: team1Roster, wins: 0, seriesStats: this.initSeriesStats(team1Roster) };
                this.team2 = { name: team2Name, roster: team2Roster, wins: 0, seriesStats: this.initSeriesStats(team2Roster) };
                this.gameNumber = 1;
                this.seriesLog = [];
                this.gameResults = [];
            }

            initSeriesStats(roster) {
                const stats = {};
                [...roster.starters, ...roster.bench].forEach(p => {
                    stats[p.name] = { pts: 0, reb: 0, ast: 0, pf: 0 };
                });
                return stats;
            }

            renderSeriesScreen() {
                const isSeriesOver = this.team1.wins >= 4 || this.team2.wins >= 4;
                let buttonHtml;
                let mvpCardHtml = '';

                if (isSeriesOver) {
                    const winner = this.team1.wins > this.team2.wins ? this.team1 : this.team2;
                    const seriesMVP = this.calculateSeriesMVP();
                    mvpCardHtml = `
                        <div class="bg-gray-800 p-6 rounded-xl shadow-lg max-w-4xl mx-auto mb-6">
                            <h3 class="text-2xl font-bold text-amber-400 mb-4 text-center">Series MVP</h3>
                            <div class="flex items-center bg-gray-900 p-4 rounded-lg">
                                <img src="${seriesMVP.img_url}" class="w-16 h-16 rounded-full mr-4">
                                <div>
                                    <p class="text-xl font-bold">${seriesMVP.name}</p>
                                    <p class="text-gray-400">
                                        (${(seriesMVP.stats.pts / (this.gameNumber - 1)).toFixed(1)} PPG, 
                                        ${(seriesMVP.stats.reb / (this.gameNumber - 1)).toFixed(1)} RPG, 
                                        ${(seriesMVP.stats.ast / (this.gameNumber - 1)).toFixed(1)} APG)
                                    </p>
                                </div>
                            </div>
                        </div>
                    `;
                    buttonHtml = `
                        <div class="flex flex-col sm:flex-row gap-4 justify-center">
                            <button id="rematch-btn" class="action-button menu-button text-white font-bold py-3 px-8 rounded-lg text-xl">Rematch</button>
                            <button id="home-btn" class="menu-button text-white font-bold py-3 px-8 rounded-lg text-xl">Home</button>
                        </div>
                    `;
                } else {
                    buttonHtml = `
                        <div class="flex flex-col sm:flex-row gap-4 justify-center">
                            <button id="sim-next-game-btn" class="action-button menu-button text-white font-bold py-3 px-8 rounded-lg text-xl">Simulate Game ${this.gameNumber}</button>
                            <button id="sim-full-series-btn" class="menu-button text-white font-bold py-3 px-8 rounded-lg text-xl">Sim Full Series</button>
                        </div>
                    `;
                }

                document.getElementById('app-container').innerHTML = `
                    <header class="text-center mb-6">
                        <h1 class="text-3xl font-bold">Best-of-7 Series</h1>
                        <p class="text-6xl font-black my-2"><span class="text-blue-400">${this.team1.wins}</span> - <span class="text-orange-400">${this.team2.wins}</span></p>
                    </header>
                    ${mvpCardHtml}
                    <div class="bg-gray-800 p-6 rounded-xl shadow-lg min-h-[200px] max-w-4xl mx-auto">
                        <h3 class="text-xl font-bold mb-4">Series Log</h3>
                        <ul class="text-gray-300 space-y-4">${this.seriesLog.join('')}</ul>
                    </div>
                    <div class="text-center mt-6">${buttonHtml}</div>
                `;
                
                if (!isSeriesOver) {
                    document.getElementById('sim-next-game-btn').addEventListener('click', () => this.playGame());
                    document.getElementById('sim-full-series-btn').addEventListener('click', () => this.simulateFullSeries());
                } else {
                    document.getElementById('rematch-btn').addEventListener('click', () => this.rematch());
                    document.getElementById('home-btn').addEventListener('click', () => App.renderHome());
                }
                
                App.addBackButton(() => App.renderRosterSetup(true));
            }
            
            rematch() {
                this.gameNumber = 1;
                this.seriesLog = [];
                this.gameResults = [];
                this.team1.wins = 0;
                this.team2.wins = 0;
                this.team1.seriesStats = this.initSeriesStats(this.team1.roster);
                this.team2.seriesStats = this.initSeriesStats(this.team2.roster);
                this.renderSeriesScreen();
            }

            playGame() {
                const game = new SeriesGame(this.team1, this.team2, this);
                game.renderGameScreen();
            }

            simulateFullSeries() {
                 while(this.team1.wins < 4 && this.team2.wins < 4) {
                    const game = new SeriesGame(this.team1, this.team2, this);
                    const result = game.simulateGame();
                    this.endGame(result);
                 }
            }

            endGame(result) {
                if (result.winner.name === this.team1.name) this.team1.wins++;
                else this.team2.wins++;
                
                [...result.team1.onCourt, ...result.team1.bench].forEach(player => {
                    this.team1.seriesStats[player.name].pts += player.stats.pts;
                    this.team1.seriesStats[player.name].reb += player.stats.reb;
                    this.team1.seriesStats[player.name].ast += player.stats.ast;
                    this.team1.seriesStats[player.name].pf += player.stats.pf;
                });
                [...result.team2.onCourt, ...result.team2.bench].forEach(player => {
                    this.team2.seriesStats[player.name].pts += player.stats.pts;
                    this.team2.seriesStats[player.name].reb += player.stats.reb;
                    this.team2.seriesStats[player.name].ast += player.stats.ast;
                    this.team2.seriesStats[player.name].pf += player.stats.pf;
                });

                this.seriesLog.unshift(result.log);
                this.gameResults.push(result.gameData);
                this.gameNumber++;
                this.renderSeriesScreen();
            }

            calculateSeriesMVP() {
                const winner = this.team1.wins > this.team2.wins ? this.team1 : this.team2;
                const winningTeamPlayers = [...winner.roster.starters, ...winner.roster.bench];

                let mvp = null;
                let maxScore = -1;

                winningTeamPlayers.forEach(player => {
                    const stats = (this.team1.seriesStats[player.name] || this.team2.seriesStats[player.name]);
                    if (stats) {
                        const mvpScore = stats.pts * 1.0 + stats.reb * 1.2 + stats.ast * 1.5 - stats.pf * 2.0;
                        if (mvpScore > maxScore) {
                            maxScore = mvpScore;
                            mvp = player;
                            mvp.stats = stats;
                        }
                    }
                });
                return mvp;
            }
            
            viewBoxScore(gameIndex) {
                const gameResult = this.gameResults[gameIndex];
                if (!gameResult) return;

                const boxScoreHtml = (team) => `
                    <div>
                        <h4 class="text-xl font-bold text-teal-300 mb-2">${team.name}</h4>
                        <table class="w-full text-left text-sm">
                            <thead><tr class="border-b border-gray-600"><th class="p-2">Player</th><th class="p-2">MIN</th><th class="p-2">PTS</th><th class="p-2">REB</th><th class="p-2">AST</th><th class="p-2">PF</th></tr></thead>
                            <tbody>
                                ${[...team.onCourt, ...team.bench].sort((a,b) => b.stats.mins - a.stats.mins).map(p => `<tr><td class="p-2">${p.name}</td><td class="p-2">${p.stats.mins}</td><td class="p-2">${p.stats.pts}</td><td class="p-2">${p.stats.reb}</td><td class="p-2">${p.stats.ast}</td><td class="p-2">${p.stats.pf}</td></tr>`).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
                document.getElementById('app-container').innerHTML = `
                    <header class="text-center mb-6">
                        <h1 class="text-3xl font-bold">Game ${gameResult.gameNumber} Box Score</h1>
                        <p class="text-xl">${gameResult.winner.name} wins ${gameResult.score}</p>
                    </header>
                    <div class="bg-gray-800 p-6 rounded-xl shadow-lg max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
                        ${boxScoreHtml(gameResult.team1)}
                        ${boxScoreHtml(gameResult.team2)}
                    </div>
                `;
                App.addBackButton(() => this.renderSeriesScreen());
            }
        }
        
        class SeriesGame {
            constructor(team1, team2, series) {
                this.team1 = JSON.parse(JSON.stringify(team1));
                this.team2 = JSON.parse(JSON.stringify(team2));
                this.series = series;
                this.gameNumber = series ? series.gameNumber : 1;
                this.score = { q1: {t1:0, t2:0}, q2: {t1:0, t2:0}, q3: {t1:0, t2:0}, q4: {t1:0, t2:0} };
                this.currentQuarter = 1;
                this.playByPlay = [];

                [this.team1, this.team2].forEach(t => {
                    [...t.roster.starters, ...t.roster.bench].forEach(p => {
                        p.stats = { pts: 0, reb: 0, ast: 0, mins: 0, pf: 0 };
                        p.stamina = 100;
                    });
                    t.onCourt = t.roster.starters;
                    t.bench = t.roster.bench;
                });
            }

            simulateGame() {
                while(this.currentQuarter <= 4) {
                    this.runQuarterSimulation();
                    this.handleSubstitutions();
                    this.currentQuarter++;
                }
                return this.finalizeGame();
            }

            renderGameScreen() {
                const t1_total = Object.values(this.score).reduce((s,q)=>s+q.t1,0);
                const t2_total = Object.values(this.score).reduce((s,q)=>s+q.t2,0);
                let buttonHtml;

                if (this.currentQuarter > 4) {
                    buttonHtml = `<button id="finish-game-btn" class="action-button menu-button text-white font-bold py-3 px-8 rounded-lg text-xl">Finalize Game</button>`;
                } else {
                    buttonHtml = `<button id="sim-quarter-btn" class="action-button menu-button text-white font-bold py-3 px-8 rounded-lg text-xl">Simulate Q${this.currentQuarter}</button>`;
                }

                document.getElementById('app-container').innerHTML = `
                    <header class="text-center mb-4">
                        <h1 class="text-3xl font-bold">Game ${this.gameNumber}</h1>
                        <p class="text-6xl font-black my-1">${t1_total} - ${t2_total}</p>
                    </header>
                    <div class="bg-gray-800 p-4 rounded-xl shadow-lg max-w-2xl mx-auto">
                        <table class="w-full text-center">
                            <thead><tr class="border-b border-gray-600"><th class="p-2">Team</th><th>Q1</th><th>Q2</th><th>Q3</th><th>Q4</th><th>Total</th></tr></thead>
                            <tbody>
                                <tr><td class="p-2 text-left font-bold text-blue-400">${this.team1.name}</td><td>${this.score.q1.t1}</td><td>${this.score.q2.t1}</td><td>${this.score.q3.t1}</td><td>${this.score.q4.t1}</td><td class="font-bold">${t1_total}</td></tr>
                                <tr><td class="p-2 text-left font-bold text-orange-400">${this.team2.name}</td><td>${this.score.q1.t2}</td><td>${this.score.q2.t2}</td><td>${this.score.q3.t2}</td><td>${this.score.q4.t2}</td><td class="font-bold">${t2_total}</td></tr>
                            </tbody>
                        </table>
                    </div>
                    <div id="play-by-play" class="mt-6 bg-gray-800 p-4 rounded-xl shadow-lg max-w-2xl mx-auto space-y-2">
                        <h3 class="text-xl font-bold mb-2 text-center text-amber-400">Quarter Highlights</h3>
                        ${this.playByPlay.join('')}
                    </div>
                    <div class="text-center mt-6">${buttonHtml}</div>
                `;

                if (this.currentQuarter > 4) {
                    document.getElementById('finish-game-btn').addEventListener('click', () => this.endGame());
                } else {
                    document.getElementById('sim-quarter-btn').addEventListener('click', () => this.simulateQuarter());
                }
            }

            simulateQuarter() {
                document.getElementById('sim-quarter-btn').disabled = true;
                document.getElementById('sim-quarter-btn').textContent = 'Simulating...';
                setTimeout(() => {
                    this.runQuarterSimulation();
                    this.handleSubstitutions();
                    this.currentQuarter++;
                    this.renderGameScreen();
                }, 500);
            }

            runQuarterSimulation() {
                const possessions = 48; 
                for (let i = 0; i < possessions; i++) {
                    this.runPossession(i % 2 === 0 ? this.team1 : this.team2);
                }
                [this.team1, this.team2].forEach(t => t.onCourt.forEach(p => p.stats.mins += 12));
            }

            handleSubstitutions() {
                [this.team1, this.team2].forEach(team => {
                    team.bench.forEach(p => p.stamina = Math.min(100, p.stamina + 15));
                    
                    for(let i = 0; i < team.onCourt.length; i++) {
                        const tiredPlayer = team.onCourt[i];
                        if (tiredPlayer.stamina < 70 && tiredPlayer.stats.mins < tiredPlayer.target_minutes) {
                            const freshPlayer = team.bench.find(p => p.pos === tiredPlayer.pos && p.stamina > 90);
                            if (freshPlayer) {
                                const freshIndex = team.bench.findIndex(p => p.name === freshPlayer.name);
                                team.onCourt[i] = freshPlayer;
                                team.bench[freshIndex] = tiredPlayer;
                            }
                        }
                    }
                });
            }

            runPossession(offense) {
                const defense = offense.name === this.team1.name ? this.team2 : this.team1;
                
                const totalUsage = offense.onCourt.reduce((sum, p) => sum + p.career_stats.usg_pct, 0);
                let randomUsage = Math.random() * totalUsage;
                let offensivePlayer;
                for(const player of offense.onCourt) {
                    randomUsage -= player.career_stats.usg_pct;
                    if(randomUsage <= 0) {
                        offensivePlayer = player;
                        break;
                    }
                }
                if (!offensivePlayer) offensivePlayer = offense.onCourt[0];

                const defender = defense.onCourt.find(p => p.pos === offensivePlayer.pos) || defense.onCourt[Math.floor(Math.random()*5)];
                
                offensivePlayer.stamina -= 2;
                defender.stamina -= 1;

                const passChance = offensivePlayer.attributes.playmaking - (offensivePlayer.career_stats.usg_pct * 1.5);
                if(Math.random() * 100 < passChance) {
                    const shooter = offense.onCourt.filter(p => p.name !== offensivePlayer.name)[Math.floor(Math.random() * 4)];
                    if (shooter) {
                         this.resolveShot(shooter, offense, defense, offensivePlayer);
                    }
                } else {
                    this.resolveShot(offensivePlayer, offense, defense, null);
                }
            }

            resolveShot(shooter, offense, defense, assister) {
                const defender = defense.onCourt.find(p => p.pos === shooter.pos) || defense.onCourt[Math.floor(Math.random()*5)];
                
                const shotTendencies = shooter.shot_tendencies;
                const totalShotWeight = shotTendencies.inside + shotTendencies.mid + shotTendencies.three;
                let randomShot = Math.random() * totalShotWeight;
                let shotType;

                if (randomShot < shotTendencies.inside) shotType = 'inside_scoring';
                else if (randomShot < shotTendencies.inside + shotTendencies.mid) shotType = 'mid_range';
                else shotType = 'three_point';

                const offRating = shooter.attributes[shotType] * (shooter.stamina / 100);
                const defRating = (shotType === 'inside_scoring' ? defender.attributes.interior_defense : defender.attributes.perimeter_defense) * (defender.stamina / 100);
                
                const baseChance = shooter.career_stats.fg_pct;
                const scoreChance = baseChance + (offRating - defRating) * 0.75;

                if(Math.random() * 100 < defender.foul_tendency * 2) {
                    defender.stats.pf++;
                }

                if(Math.random() * 100 < scoreChance) {
                    const points = shotType === 'three_point' ? 3 : 2;
                    this.score[`q${this.currentQuarter}`][offense.name === this.team1.name ? 't1' : 't2'] += points;
                    shooter.stats.pts += points;
                    if(assister) assister.stats.ast++;
                } else {
                    const allPlayers = [...offense.onCourt, ...defense.onCourt];
                    const totalRebChance = allPlayers.reduce((sum, player) => sum + player.attributes.rebounding * (player.stamina/100), 0);
                    let randomReb = Math.random() * totalRebChance;
                    for(const player of allPlayers) {
                        randomReb -= player.attributes.rebounding * (player.stamina/100);
                        if(randomReb <= 0) {
                            player.stats.reb++;
                            break;
                        }
                    }
                }
            }
            
            finalizeGame() {
                const t1_total = Object.values(this.score).reduce((sum, q) => sum + q.t1, 0);
                const t2_total = Object.values(this.score).reduce((sum, q) => sum + q.t2, 0);
                const winner = t1_total >= t2_total ? this.team1 : this.team2;
                const allPlayers = [...this.team1.onCourt, ...this.team1.bench, ...this.team2.onCourt, ...this.team2.bench];
                
                const gameMVP = this.calculateGameMVP(allPlayers);

                const gameResultForLog = {
                    gameNumber: this.gameNumber,
                    winner: winner,
                    score: `${Math.max(t1_total, t2_total)} - ${Math.min(t1_total, t2_total)}`,
                    team1: this.team1,
                    team2: this.team2
                };
                
                const gameLog = `
                    <li class="border-b border-gray-700 pb-3 mb-3">
                        <div class="flex justify-between items-center">
                            <p class="font-bold text-lg">${winner.name} wins ${Math.max(t1_total, t2_total)} - ${Math.min(t1_total, t2_total)}</p>
                            ${this.series ? `<button class="view-box-score-btn menu-button text-xs py-1 px-3 rounded" data-game-index="${this.series.gameResults.length}">View Box Score</button>` : ''}
                        </div>
                        <div class="text-sm text-gray-400 mt-2">
                           <span><strong>Game MVP:</strong> ${gameMVP.name} (${gameMVP.stats.pts} PTS, ${gameMVP.stats.reb} REB, ${gameMVP.stats.ast} AST)</span>
                        </div>
                    </li>
                `;
                return { winner, log: gameLog, gameData: gameResultForLog, team1: this.team1, team2: this.team2 };
            }

            calculateGameMVP(allPlayers) {
                let mvp = allPlayers[0];
                let maxScore = -1;
                allPlayers.forEach(p => {
                    const score = p.stats.pts * 1.0 + p.stats.reb * 1.2 + p.stats.ast * 1.5 - p.stats.pf * 2.0;
                    if (score > maxScore) {
                        maxScore = score;
                        mvp = p;
                    }
                });
                return mvp;
            }

            endGame() {
                const result = this.finalizeGame();
                if (this.series) {
                    this.series.endGame(result);
                } else {
                    this.renderPostGame(result.gameData);
                }
            }

            renderPostGame(gameResult) {
                const allPlayers = [...gameResult.team1.onCourt, ...gameResult.team1.bench, ...gameResult.team2.onCourt, ...gameResult.team2.bench];
                const mvp = this.calculateGameMVP(allPlayers);

                const boxScoreHtml = (team) => `
                    <div>
                        <h4 class="text-xl font-bold text-teal-300 mb-2">${team.name}</h4>
                        <table class="w-full text-left text-sm">
                            <thead><tr class="border-b border-gray-600"><th class="p-2">Player</th><th class="p-2">MIN</th><th class="p-2">PTS</th><th class="p-2">REB</th><th class="p-2">AST</th><th class="p-2">PF</th></tr></thead>
                            <tbody>
                                ${[...team.onCourt, ...team.bench].sort((a,b) => b.stats.mins - a.stats.mins).map(p => `<tr><td class="p-2">${p.name}</td><td class="p-2">${p.stats.mins}</td><td class="p-2">${p.stats.pts}</td><td class="p-2">${p.stats.reb}</td><td class="p-2">${p.stats.ast}</td><td class="p-2">${p.stats.pf}</td></tr>`).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
                document.getElementById('app-container').innerHTML = `
                    <header class="text-center mb-6">
                        <h1 class="text-3xl font-bold">Final Score</h1>
                        <p class="text-xl">${gameResult.winner.name} wins ${gameResult.score}</p>
                    </header>
                    <div class="bg-gray-800 p-6 rounded-xl shadow-lg max-w-4xl mx-auto mb-6">
                        <h3 class="text-2xl font-bold text-amber-400 mb-4 text-center">Game MVP</h3>
                        <div class="flex items-center bg-gray-900 p-4 rounded-lg">
                            <img src="${mvp.img_url}" class="w-16 h-16 rounded-full mr-4">
                            <div>
                                <p class="text-xl font-bold">${mvp.name}</p>
                                <p class="text-gray-400">${mvp.stats.pts} PTS | ${mvp.stats.reb} REB | ${mvp.stats.ast} AST | ${mvp.stats.pf} PF</p>
                            </div>
                        </div>
                    </div>
                    <div class="bg-gray-800 p-6 rounded-xl shadow-lg max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
                        ${boxScoreHtml(gameResult.team1)}
                        ${boxScoreHtml(gameResult.team2)}
                    </div>
                     <div class="text-center mt-6 flex justify-center gap-4">
                        <button id="play-again-btn" class="menu-button text-white font-bold py-3 px-8 rounded-lg text-xl">Play Again</button>
                        <button id="main-menu-btn" class="menu-button text-white font-bold py-3 px-8 rounded-lg text-xl">Main Menu</button>
                    </div>
                `;
                document.getElementById('play-again-btn').addEventListener('click', () => App.renderRosterSetup(false));
                document.getElementById('main-menu-btn').addEventListener('click', () => App.renderHome());
                App.addBackButton(() => App.renderRosterSetup(false));
            }
        }

        document.addEventListener('DOMContentLoaded', () => App.init());
    </script>
</body>
</html>
