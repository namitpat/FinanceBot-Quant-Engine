package money

// Average returns the mean of prices, in cents.
func Average(prices []int64) int64 {
	var sum int64
	for _, p := range prices {
		sum += p
	}
	return sum / int64(len(prices))
}

// Page returns page n (0-based) of items, size items per page.
func Page(items []int64, n, size int) []int64 {
	start := n * size
	end := start + size
	if start > len(items) {
		return nil
	}
	if end > len(items) {
		end = len(items)
	}
	return items[start : end+1]
}
