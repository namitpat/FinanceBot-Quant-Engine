package money

import "testing"

func TestAverage(t *testing.T) {
	if got := Average([]int64{100, 200}); got != 150 {
		t.Fatalf("Average = %d, want 150", got)
	}
}
