{- tsort.hs
 - A Haskell clone of the GNU coreutil tsort
 -
 - Just practicing Haskell, I decided to start implementing coreutils
 -
 - Then I realized most of them are here:
 - http://haskell.org/haskellwiki/Simple_Unix_tools
 -
 - But this one's not, so I did it.
 -
 - Chris Johnson
 - 2009
 -}

import System.Environment
import System.Exit

-- Bring nub (uniq) into scope
import Data.List

contains :: Eq a => [a] -> a -> Bool
contains = flip elem

{-
 - tsort - total sort
 -
 - Takes a collection of sequences which describe partial orderings and returns
 - a sequence that satisfies all of the partial orderings.
-}
tsort :: Eq a => [[a]] -> [a]
tsort [] = []
		 -- Drop empty lists
tsort seqs = let seqs'      = filter (not . null) seqs
		 heads      = nub (map head seqs')
		 -- Tails of sequences are inaccessible
		 restricted = nub (tail =<< seqs') -- (=<<) acts like concatMap
		 -- Heads that are not restricted are just grand
		 winners    = filter (not . contains restricted) heads
		 -- Remove any winners from the beginning of our sequences
		 losers     = map (dropWhile (contains winners)) seqs'
		in if null winners && (not . null) losers
			then error "No ordering exists"
			else winners ++ tsort losers

{- And to pull this out of its hermetic seal -}

-- Shamelessly copied, studied, and (mostly) understood
main :: IO String
main = getArgs >>= parse >>= putStr . run >> exit

-- Right now we can only handle up to one argument.
-- But that's okay. We're doing no worse than the original.
parse :: [String] -> IO String
parse ["-h"]	= putStr help >> exit
parse ["-v"]	= putStr version >> exit
parse []	= getContents
parse [f]	= readFile f
parse (x:xs)	= parse [x]

-- Whee! The last line is slightly changed.
help :: String
help = unlines ["Usage: tsort [OPTION] [FILE]",
  "Write totally ordered list consistent with the partial ordering in FILE.",
  "With no FILE, or when FILE is -, read standard input.",
  "",
  "      --help     display this help and exit",
  "      --version  output version information and exit",
  "",
  "Report bugs to <effigies@gmail.com>."]

version :: String
version = unlines ["tsort 0.01",
  "Academic Free License",
  "Copy what you like."]

-- Similarly copied
run :: String -> String
run = unlines . tsort . (map words) . lines

exit :: IO String
exit = exitWith ExitSuccess
