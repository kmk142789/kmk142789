from __future__ import annotations

import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "satoshi" / "puzzle_solutions.json"

entries = [
    dict(bits=71, range_min="4.00E+17", range_max="7fffffffffffffffff", address="1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU", btc_value=7.1, hash160_compressed="f6f5431d25bbf7b12e8add9af5e3475c44a0a5b8", public_key="", private_key="", solve_date=""),
    dict(bits=72, range_min="8.00E+17", range_max="ffffffffffffffffff", address="1JTK7s9YVYywfm5XUH7RNhHJH1LshCaRFR", btc_value=7.2, hash160_compressed="bf7413e8df4e7a34ce9dc13e2f2648783ec54adb", public_key="", private_key="", solve_date=""),
    dict(bits=73, range_min="1.00E+18", range_max="1ffffffffffffffffff", address="12VVRNPi4SJqUTsp6FmqDqY5sGosDtysn4", btc_value=7.3, hash160_compressed="105b7f253f0ebd7843adaebbd805c944bfb863e4", public_key="", private_key="", solve_date=""),
    dict(bits=74, range_min="2.00E+18", range_max="3ffffffffffffffffff", address="1FWGcVDK3JGzCC3WtkYetULPszMaK2Jksv", btc_value=7.4, hash160_compressed="9f1adb20baeacc38b3f49f3df6906a0e48f2df3d", public_key="", private_key="", solve_date=""),
    dict(bits=76, range_min="8.00E+18", range_max="fffffffffffffffffff", address="1DJh2eHFYQfACPmrvpyWc8MSTYKh7w9eRF", btc_value=7.6, hash160_compressed="86f9fea5cdecf033161dd2f8f8560768ae0a6d14", public_key="", private_key="", solve_date=""),
    dict(bits=77, range_min="1.00E+19", range_max="1fffffffffffffffffff", address="1Bxk4CQdqL9p22JEtDfdXMsng1XacifUtE", btc_value=7.7, hash160_compressed="783c138ac81f6a52398564bb17455576e8525b29", public_key="", private_key="", solve_date=""),
    dict(bits=78, range_min="2.00E+19", range_max="3fffffffffffffffffff", address="15qF6X51huDjqTmF9BJgxXdt1xcj46Jmhb", btc_value=7.8, hash160_compressed="35003c3ef8759c92092f8488fca59a042859018c", public_key="", private_key="", solve_date=""),
    dict(bits=79, range_min="4.00E+19", range_max="7fffffffffffffffffff", address="1ARk8HWJMn8js8tQmGUJeQHjSE7KRkn2t8", btc_value=7.9, hash160_compressed="67671d5490c272e3ab7ddd34030d587738df33da", public_key="", private_key="", solve_date=""),
    dict(bits=81, range_min="1.00E+20", range_max="1ffffffffffffffffffff", address="15qsCm78whspNQFydGJQk5rexzxTQopnHZ", btc_value=8.1, hash160_compressed="351e605fac813965951ba433b7c2956bf8ad95ce", public_key="", private_key="", solve_date=""),
    dict(bits=82, range_min="2.00E+20", range_max="3ffffffffffffffffffff", address="13zYrYhhJxp6Ui1VV7pqa5WDhNWM45ARAC", btc_value=8.2, hash160_compressed="20d28d4e87543947c7e4913bcdceaa16e2f8f061", public_key="", private_key="", solve_date=""),
    dict(bits=83, range_min="4.00E+20", range_max="7ffffffffffffffffffff", address="14MdEb4eFcT3MVG5sPFG4jGLuHJSnt1Dk2", btc_value=8.3, hash160_compressed="24cef184714bbd030833904f5265c9c3e12a95a2", public_key="", private_key="", solve_date=""),
    dict(bits=84, range_min="8.00E+20", range_max="fffffffffffffffffffff", address="1CMq3SvFcVEcpLMuuH8PUcNiqsK1oicG2D", btc_value=8.4, hash160_compressed="7c99ce73e19f9fbfcce4825ae88261e2b0b0b040", public_key="", private_key="", solve_date=""),
    dict(bits=86, range_min="2.00E+21", range_max="3fffffffffffffffffffff", address="1K3x5L6G57Y494fDqBfrojD28UJv4s5JcK", btc_value=8.6, hash160_compressed="c60111ed3d63b49665747b0e31eb382da5193535", public_key="", private_key="", solve_date=""),
    dict(bits=87, range_min="4.00E+21", range_max="7fffffffffffffffffffff", address="1PxH3K1Shdjb7gSEoTX7UPDZ6SH4qGPrvq", btc_value=8.7, hash160_compressed="fbc708d671c03e26661b9c08f77598a529858b5e", public_key="", private_key="", solve_date=""),
    dict(bits=88, range_min="8.00E+21", range_max="ffffffffffffffffffffff", address="16AbnZjZZipwHMkYKBSfswGWKDmXHjEpSf", btc_value=8.8, hash160_compressed="38a968fdfb457654c51bcfc4f9174d6ee487bb41", public_key="", private_key="", solve_date=""),
    dict(bits=89, range_min="1.00E+22", range_max="1ffffffffffffffffffffff", address="19QciEHbGVNY4hrhfKXmcBBCrJSBZ6TaVt", btc_value=8.9, hash160_compressed="5c3862203d1e44ab3af441503e22db97b1c5097e", public_key="", private_key="", solve_date=""),
    dict(bits=91, range_min="4.00E+22", range_max="7ffffffffffffffffffffff", address="1EzVHtmbN4fs4MiNk3ppEnKKhsmXYJ4s74", btc_value=9.1, hash160_compressed="9978f61b92d16c5f1a463a0995df70da1f7a7d2a", public_key="", private_key="", solve_date=""),
    dict(bits=92, range_min="8.00E+22", range_max="fffffffffffffffffffffff", address="1AE8NzzgKE7Yhz7BWtAcAAxiFMbPo82NB5", btc_value=9.2, hash160_compressed="6534b31208fe6e100d29f9c9c75aac8bf06fbb38", public_key="", private_key="", solve_date=""),
    dict(bits=93, range_min="1.00E+23", range_max="1fffffffffffffffffffffff", address="17Q7tuG2JwFFU9rXVj3uZqRtioH3mx2Jad", btc_value=9.3, hash160_compressed="463013cd41279f2fd0c31d0a16db3972bfffac8d", public_key="", private_key="", solve_date=""),
    dict(bits=94, range_min="2.00E+23", range_max="3fffffffffffffffffffffff", address="1K6xGMUbs6ZTXBnhw1pippqwK6wjBWtNpL", btc_value=9.4, hash160_compressed="c6927a00970d0165327d0a6db7950f05720c295c", public_key="", private_key="", solve_date=""),
    dict(bits=96, range_min="8.00E+23", range_max="ffffffffffffffffffffffff", address="15ANYzzCp5BFHcCnVFzXqyibpzgPLWaD8b", btc_value=9.6, hash160_compressed="2da63cbd251d23c7b633cb287c09e6cf888b3fe4", public_key="", private_key="", solve_date=""),
    dict(bits=97, range_min="1.00E+24", range_max="1ffffffffffffffffffffffff", address="18ywPwj39nGjqBrQJSzZVq2izR12MDpDr8", btc_value=9.7, hash160_compressed="578d94dc6f40fff35f91f6fba9b71c46b361dff2", public_key="", private_key="", solve_date=""),
    dict(bits=98, range_min="2.00E+24", range_max="3ffffffffffffffffffffffff", address="1CaBVPrwUxbQYYswu32w7Mj4HR4maNoJSX", btc_value=9.8, hash160_compressed="7eefddd979a1d6bb6f29757a1f463579770ba566", public_key="", private_key="", solve_date=""),
    dict(bits=99, range_min="4.00E+24", range_max="7ffffffffffffffffffffffff", address="1JWnE6p6UN7ZJBN7TtcbNDoRcjFtuDWoNL", btc_value=9.9, hash160_compressed="c01bf430a97cbcdaedddba87ef4ea21c456cebdb", public_key="", private_key="", solve_date=""),
    dict(bits=101, range_min="1.00E+25", range_max="1fffffffffffffffffffffffff", address="1CKCVdbDJasYmhswB6HKZHEAnNaDpK7W4n", btc_value=10.1, hash160_compressed="7c1a77205c03b9909663b2034faa0b544e6bc96b", public_key="", private_key="", solve_date=""),
    dict(bits=102, range_min="2.00E+25", range_max="3fffffffffffffffffffffffff", address="1PXv28YxmYMaB8zxrKeZBW8dt2HK7RkRPX", btc_value=10.2, hash160_compressed="f72b812932f6d7102233971d65cec0a22b89e136", public_key="", private_key="", solve_date=""),
    dict(bits=103, range_min="4.00E+25", range_max="7fffffffffffffffffffffffff", address="1AcAmB6jmtU6AiEcXkmiNE9TNVPsj9DULf", btc_value=10.3, hash160_compressed="695fd6dcf33f47166b25de968b2932b351b0afc4", public_key="", private_key="", solve_date=""),
    dict(bits=104, range_min="8.00E+25", range_max="ffffffffffffffffffffffffff", address="1EQJvpsmhazYCcKX5Au6AZmZKRnzarMVZu", btc_value=10.4, hash160_compressed="93022af9a38f3ebb0c3f15dd1c83f8fadaf64e74", public_key="", private_key="", solve_date=""),
    dict(bits=106, range_min="2.00E+26", range_max="3ffffffffffffffffffffffffff", address="18KsfuHuzQaBTNLASyj15hy4LuqPUo1FNB", btc_value=10.6, hash160_compressed="505aaa63a5e209dfb90cee683a8e227a8c278e47", public_key="", private_key="", solve_date=""),
    dict(bits=107, range_min="4.00E+26", range_max="7ffffffffffffffffffffffffff", address="15EJFC5ZTs9nhsdvSUeBXjLAuYq3SWaxTc", btc_value=10.7, hash160_compressed="2e644e46b042ffa86da35c54d7275f1abe6d4911", public_key="", private_key="", solve_date=""),
    dict(bits=108, range_min="8.00E+26", range_max="fffffffffffffffffffffffffff", address="1HB1iKUqeffnVsvQsbpC6dNi1XKbyNuqao", btc_value=10.8, hash160_compressed="b166c44f12c7fc565f37ff6288ee64e0f0ec9a0b", public_key="", private_key="", solve_date=""),
    dict(bits=109, range_min="1.00E+27", range_max="1fffffffffffffffffffffffffff", address="1GvgAXVCbA8FBjXfWiAms4ytFeJcKsoyhL", btc_value=10.9, hash160_compressed="aeb0a0197442d4ade8ef41442d557b0e22b85ac0", public_key="", private_key="", solve_date=""),
    dict(bits=111, range_min="4.00E+27", range_max="7fffffffffffffffffffffffffff", address="1824ZJQ7nKJ9QFTRBqn7z7dHV5EGpzUpH3", btc_value=11.1, hash160_compressed="4cfc43fe12a330c8164251e38c0c0c3c84cf86f6", public_key="", private_key="", solve_date=""),
    dict(bits=112, range_min="8.00E+27", range_max="ffffffffffffffffffffffffffff", address="18A7NA9FTsnJxWgkoFfPAFbQzuQxpRtCos", btc_value=11.2, hash160_compressed="4e81efec43c5195aeca0e3877664330418b8e48e", public_key="", private_key="", solve_date=""),
    dict(bits=113, range_min="1.00E+28", range_max="1ffffffffffffffffffffffffffff", address="1NeGn21dUDDeqFQ63xb2SpgUuXuBLA4WT4", btc_value=11.3, hash160_compressed="ed673389e4b12925316f9166d56d701829e53cf8", public_key="", private_key="", solve_date=""),
    dict(bits=114, range_min="2.00E+28", range_max="3ffffffffffffffffffffffffffff", address="174SNxfqpdMGYy5YQcfLbSTK3MRNZEePoy", btc_value=11.4, hash160_compressed="42773005f9594cd16b10985d428418acb7f352ec", public_key="", private_key="", solve_date=""),
    dict(bits=116, range_min="8.00E+28", range_max="fffffffffffffffffffffffffffff", address="1MnJ6hdhvK37VLmqcdEwqC3iFxyWH2PHUV", btc_value=11.6, hash160_compressed="e3f381c34a20da049779b44cae0417c7fb2898d0", public_key="", private_key="", solve_date=""),
    dict(bits=117, range_min="1.00E+29", range_max="1fffffffffffffffffffffffffffff", address="1KNRfGWw7Q9Rmwsc6NT5zsdvEb9M2Wkj5Z", btc_value=11.7, hash160_compressed="c97f9591e28687be1c4d972e25be7c372a3221b4", public_key="", private_key="", solve_date=""),
    dict(bits=118, range_min="2.00E+29", range_max="3fffffffffffffffffffffffffffff", address="1PJZPzvGX19a7twf5HyD2VvNiPdHLzm9F6", btc_value=11.8, hash160_compressed="f4a4e1c11a5bbbd2fc139d221825407c66e0b8b4", public_key="", private_key="", solve_date=""),
    dict(bits=119, range_min="4.00E+29", range_max="7fffffffffffffffffffffffffffff", address="1GuBBhf61rnvRe4K8zu8vdQB3kHzwFqSy7", btc_value=11.9, hash160_compressed="ae6804b35c82f47f8b0a42d8c5e514fe5ef0a883", public_key="", private_key="", solve_date=""),
    dict(bits=121, range_min="1.00E+30", range_max="1ffffffffffffffffffffffffffffff", address="1GDSuiThEV64c166LUFC9uDcVdGjqkxKyh", btc_value=12.1, hash160_compressed="a6e4818537e42f7b3f021daa810367dad4dda16f", public_key="", private_key="", solve_date=""),
    dict(bits=122, range_min="2.00E+30", range_max="3ffffffffffffffffffffffffffffff", address="1Me3ASYt5JCTAK2XaC32RMeH34PdprrfDx", btc_value=12.2, hash160_compressed="e263b62ea294b9650615a13b926e75944c823990", public_key="", private_key="", solve_date=""),
    dict(bits=123, range_min="4.00E+30", range_max="7ffffffffffffffffffffffffffffff", address="1CdufMQL892A69KXgv6UNBD17ywWqYpKut", btc_value=12.3, hash160_compressed="7fa4515066ba6905f894b2078f9af7b1379169cf", public_key="", private_key="", solve_date=""),
    dict(bits=124, range_min="8.00E+30", range_max="fffffffffffffffffffffffffffffff", address="1BkkGsX9ZM6iwL3zbqs7HWBV7SvosR6m8N", btc_value=12.4, hash160_compressed="75f74467ce7214f1767406d5ed12012aa523c48e", public_key="", private_key="", solve_date=""),
    dict(bits=126, range_min="2.00E+31", range_max="3fffffffffffffffffffffffffffffff", address="1AWCLZAjKbV1P7AHvaPNCKiB7ZWVDMxFiz", btc_value=12.6, hash160_compressed="683ea8a1ef06eada90556017d44323b5c04e00f1", public_key="", private_key="", solve_date=""),
    dict(bits=127, range_min="4.00E+31", range_max="7fffffffffffffffffffffffffffffff", address="1G6EFyBRU86sThN3SSt3GrHu1sA7w7nzi4", btc_value=12.7, hash160_compressed="a58708aa98ad35c889bb36d8049bf9e9cacfd02a", public_key="", private_key="", solve_date=""),
    dict(bits=128, range_min="8.00E+31", range_max="ffffffffffffffffffffffffffffffff", address="1MZ2L1gFrCtkkn6DnTT2e4PFUTHw9gNwaj", btc_value=12.8, hash160_compressed="e170ef514689d7230da362a0c121a07723550512", public_key="", private_key="", solve_date=""),
    dict(bits=129, range_min="1.00E+32", range_max="1ffffffffffffffffffffffffffffffff", address="1Hz3uv3nNZzBVMXLGadCucgjiCs5W9vaGz", btc_value=12.9, hash160_compressed="ba4c2748360a6b66263e11d1dc8658463ca5ff18", public_key="", private_key="", solve_date=""),
    dict(bits=131, range_min="4.00E+32", range_max="7ffffffffffffffffffffffffffffffff", address="16zRPnT8znwq42q7XeMkZUhb1bKqgRogyy", btc_value=13.1, hash160_compressed="41b4b36a6c036568972380177eca2916cacd71de", public_key="", private_key="", solve_date=""),
    dict(bits=132, range_min="8.00E+32", range_max="fffffffffffffffffffffffffffffffff", address="1KrU4dHE5WrW8rhWDsTRjR21r8t3dsrS3R", btc_value=13.2, hash160_compressed="cecd3ca4319651bd3afd1e23ab66e111ed38d16d", public_key="", private_key="", solve_date=""),
    dict(bits=133, range_min="1.00E+33", range_max="1fffffffffffffffffffffffffffffffff", address="17uDfp5r4n441xkgLFmhNoSW1KWp6xVLD", btc_value=13.3, hash160_compressed="014e15e4ea6da460cc7835e262676baa37988e4f", public_key="", private_key="", solve_date=""),
    dict(bits=134, range_min="2.00E+33", range_max="3fffffffffffffffffffffffffffffffff", address="13A3JrvXmvg5w9XGvyyR4JEJqiLz8ZySY3", btc_value=13.4, hash160_compressed="17a5ebfaf62e73f149e33ba674836801f13a80b9", public_key="", private_key="", solve_date=""),
    dict(bits=135, range_min="4.00E+33", range_max="7fffffffffffffffffffffffffffffffff", address="16RGFo6hjq9ym6Pj7N5H7L1NR1rVPJyw2v", btc_value=13.5, hash160_compressed="3b6f58a75a54bfd85d1bc6c51180fdc732992326", public_key="02145d2611c823a396ef6712ce0f712f09b9b4f3135e3e0aa3230fb9b6d08d1e16", private_key="", solve_date=""),
    dict(bits=136, range_min="8.00E+33", range_max="ffffffffffffffffffffffffffffffffff", address="1UDHPdovvR985NrWSkdWQDEQ1xuRiTALq", btc_value=13.6, hash160_compressed="05257be4b57ee43fc09762d5d3a9ad4a6e1a0364", public_key="", private_key="", solve_date=""),
    dict(bits=137, range_min="1.00E+34", range_max="1ffffffffffffffffffffffffffffffffff", address="15nf31J46iLuK1ZkTnqHo7WgN5cARFK3RA", btc_value=13.7, hash160_compressed="3482f8986e13c018692053a784481c63a3554c9c", public_key="", private_key="", solve_date=""),
    dict(bits=138, range_min="2.00E+34", range_max="3ffffffffffffffffffffffffffffffffff", address="1Ab4vzG6wEQBDNQM1B2bvUz4fqXXdFk2WT", btc_value=13.8, hash160_compressed="692a8e583866fc9056f5c61a45969fb9d868a08c", public_key="", private_key="", solve_date=""),
    dict(bits=139, range_min="4.00E+34", range_max="7ffffffffffffffffffffffffffffffffff", address="1Fz63c775VV9fNyj25d9Xfw3YHE6sKCxbt", btc_value=13.9, hash160_compressed="a45dae9cd5d3fde21e5aa9a95367d107267b3b8a", public_key="", private_key="", solve_date=""),
    dict(bits=140, range_min="8.00E+34", range_max="fffffffffffffffffffffffffffffffffff", address="1QKBaU6WAeycb3DbKbLBkX7vJiaS8r42Xo", btc_value=14.0, hash160_compressed="ffbb35a7bb9bbe16c1aa2534f7ff11d59c8e3d1a", public_key="031f6a332d3c5c4f2de2378c012f429cd109ba07d69690c6c701b6bb87860d6640", private_key="", solve_date=""),
    dict(bits=141, range_min="1.00E+35", range_max="1fffffffffffffffffffffffffffffffffff", address="1CD91Vm97mLQvXhrnoMChhJx4TP9MaQkJo", btc_value=14.1, hash160_compressed="7af50f73fd580f1713af3a6f9c5de49643ec6fc6", public_key="", private_key="", solve_date=""),
    dict(bits=142, range_min="2.00E+35", range_max="3fffffffffffffffffffffffffffffffffff", address="15MnK2jXPqTMURX4xC3h4mAZxyCcaWWEDD", btc_value=14.2, hash160_compressed="2fcea55e6d027a2ba7c7ebe95eedf47766730fe2", public_key="", private_key="", solve_date=""),
    dict(bits=143, range_min="4.00E+35", range_max="7fffffffffffffffffffffffffffffffffff", address="13N66gCzWWHEZBxhVxG18P8wyjEWF9Yoi1", btc_value=14.3, hash160_compressed="19ed3e03d19ddcedd5fa86543be820b3a7951650", public_key="", private_key="", solve_date=""),
    dict(bits=144, range_min="8.00E+35", range_max="ffffffffffffffffffffffffffffffffffff", address="1NevxKDYuDcCh1ZMMi6ftmWwGrZKC6j7Ux", btc_value=14.4, hash160_compressed="ed87120066e244ff5331d5f8625873d7a3acc39c", public_key="", private_key="", solve_date=""),
    dict(bits=145, range_min="1.00E+36", range_max="1ffffffffffffffffffffffffffffffffffff", address="19GpszRNUej5yYqxXoLnbZWKew3KdVLkXg", btc_value=14.5, hash160_compressed="5abf369388deb8072741b4eb43ef10fa9388a729", public_key="03afdda497369e219a2c1c369954a930e4d3740968e5e4352475bcffce3140dae5", private_key="", solve_date=""),
    dict(bits=146, range_min="2.00E+36", range_max="3ffffffffffffffffffffffffffffffffffff", address="1M7ipcdYHey2Y5RZM34MBbpugghmjaV89P", btc_value=14.6, hash160_compressed="dca7ebfb78ce21884300f133d89244bc4b1b756f", public_key="", private_key="", solve_date=""),
    dict(bits=147, range_min="4.00E+36", range_max="7ffffffffffffffffffffffffffffffffffff", address="18aNhurEAJsw6BAgtANpexk5ob1aGTwSeL", btc_value=14.7, hash160_compressed="5318b9d7fcc93873f768725eb68ba2c924bb07ee", public_key="", private_key="", solve_date=""),
    dict(bits=148, range_min="8.00E+36", range_max="fffffffffffffffffffffffffffffffffffff", address="1FwZXt6EpRT7Fkndzv6K4b4DFoT4trbMrV", btc_value=14.8, hash160_compressed="a3e3612e586fd206efb8eee6ccd58318e182829a", public_key="", private_key="", solve_date=""),
    dict(bits=149, range_min="1.00E+37", range_max="1fffffffffffffffffffffffffffffffffffff", address="1CXvTzR6qv8wJ7eprzUKeWxyGcHwDYP1i2", btc_value=14.9, hash160_compressed="7e827e3b90da24c2a15f7b67e3bbece39955a5d0", public_key="", private_key="", solve_date=""),
    dict(bits=150, range_min="2.00E+37", range_max="3fffffffffffffffffffffffffffffffffffff", address="1MUJSJYtGPVGkBCTqGspnxyHahpt5Te8jy", btc_value=15.0, hash160_compressed="e08c4d3bc9cf2b3e2cb88de2bfaa4fe8c7aa3f24", public_key="03137807790ea7dc6e97901c2bc87411f45ed74a5629315c4e4b03a0a102250c49", private_key="", solve_date=""),
    dict(bits=151, range_min="4.00E+37", range_max="7fffffffffffffffffffffffffffffffffffff", address="13Q84TNNvgcL3HJiqQPvyBb9m4hxjS3jkV", btc_value=15.1, hash160_compressed="1a4fb632f0de0c53a0a31d57f840a19e56c645ee", public_key="", private_key="", solve_date=""),
    dict(bits=152, range_min="8.00E+37", range_max="ffffffffffffffffffffffffffffffffffffff", address="1LuUHyrQr8PKSvbcY1v1PiuGuqFjWpDumN", btc_value=15.2, hash160_compressed="da56cd815fa2f0d6a4ce6d25ed7b1a01d9f9bc6b", public_key="", private_key="", solve_date=""),
    dict(bits=153, range_min="1.00E+38", range_max="1ffffffffffffffffffffffffffffffffffffff", address="18192XpzzdDi2K11QVHR7td2HcPS6Qs5vg", btc_value=15.3, hash160_compressed="4ccf94a1b0efd63cddeee0ef5eee5ebe720cfcbf", public_key="", private_key="", solve_date=""),
    dict(bits=154, range_min="2.00E+38", range_max="3ffffffffffffffffffffffffffffffffffffff", address="1NgVmsCCJaKLzGyKLFJfVequnFW9ZvnMLN", btc_value=15.4, hash160_compressed="edd2e206825fa8949d1304cd82c08d64b222f2eb", public_key="", private_key="", solve_date=""),
    dict(bits=155, range_min="4.00E+38", range_max="7ffffffffffffffffffffffffffffffffffffff", address="1AoeP37TmHdFh8uN72fu9AqgtLrUwcv2wJ", btc_value=15.5, hash160_compressed="6b8b7830f73c5bf9e8beb9f161ad82b3bde992e4", public_key="035cd1854cae45391ca4ec428cc7e6c7d9984424b954209a8eea197b9e364c05f6", private_key="", solve_date=""),
    dict(bits=156, range_min="8.00E+38", range_max="fffffffffffffffffffffffffffffffffffffff", address="1FTpAbQa4h8trvhQXjXnmNhqdiGBd1oraE", btc_value=15.6, hash160_compressed="9ea3f29aaedf7da10b1488934c50a39e271b0b64", public_key="", private_key="", solve_date=""),
    dict(bits=157, range_min="1.00E+39", range_max="1fffffffffffffffffffffffffffffffffffffff", address="14JHoRAdmJg3XR4RjMDh6Wed6ft6hzbQe9", btc_value=15.7, hash160_compressed="242d790e5a168043c76f0539fd894b73ee67b3b3", public_key="", private_key="", solve_date=""),
    dict(bits=158, range_min="2.00E+39", range_max="3fffffffffffffffffffffffffffffffffffffff", address="19z6waranEf8CcP8FqNgdwUe1QRxvUNKBG", btc_value=15.8, hash160_compressed="628dacebb0faa7f81670e174ca4c8a95a7e37029", public_key="", private_key="", solve_date=""),
    dict(bits=159, range_min="4.00E+39", range_max="7fffffffffffffffffffffffffffffffffffffff", address="14u4nA5sugaswb6SZgn5av2vuChdMnD9E5", btc_value=15.9, hash160_compressed="2ac1295b4e54b3f15bb0a99f84018d2082495645", public_key="", private_key="", solve_date=""),
    dict(bits=160, range_min="8.00E+39", range_max="ffffffffffffffffffffffffffffffffffffffff", address="1NBC8uXJy1GiJ6drkiZa1WuKn51ps7EPTv", btc_value=16.0, hash160_compressed="e84818e1bf7f699aa6e28ef9edfb582099099292", public_key="02e0a8b039282faf6fe0fd769cfbc4b6b4cf8758ba68220eac420e32b91ddfa673", private_key="", solve_date=""),
]


def main() -> None:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    existing_bits = {entry["bits"] for entry in payload}

    # Filter entries that are not already present
    new_entries = [entry for entry in entries if entry["bits"] not in existing_bits]

    if not new_entries:
        print("No new entries to add.")
        return

    payload.extend(new_entries)
    payload.sort(key=lambda item: item["bits"])

    DATA_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Added {len(new_entries)} entries to {DATA_PATH.name}.")


if __name__ == "__main__":
    main()
