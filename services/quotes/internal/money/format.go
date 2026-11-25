package money

import "fmt"

// Dollars formats an amount in cents as dollars, e.g. 1234 -> "12.34".
func Dollars(cents int64) string {
	return fmt.Sprintf("%d.%d", cents/100, cents%100)
}
