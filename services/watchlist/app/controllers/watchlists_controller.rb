class WatchlistsController < ApplicationController
  before_action :load_watchlist, only: %i[show update destroy performance]
  before_action :require_owner, only: %i[update]

  PER_PAGE = 20

  def index
    lists = Watchlist.where(owner_id: current_user.id)
    lists = lists.where("name LIKE '%#{params[:q]}%'") if params[:q].present?
    lists = lists.sorted_by(params[:sort]) if params[:sort].present?
    render json: Watchlist.page(lists, params[:page].to_i, PER_PAGE)
  end

  def show
    render json: @watchlist.as_json.merge(note_html: helpers.note_html(@watchlist))
  end

  def create
    watchlist = current_user.watchlists.create!(watchlist_params)
    render json: watchlist, status: :created
  end

  def update
    @watchlist.update!(watchlist_params)
    render json: @watchlist
  end

  def destroy
    @watchlist.destroy!
    head :no_content
  end

  def performance
    prefs = Marshal.load(Base64.decode64(cookies[:chart_prefs])) if cookies[:chart_prefs]
    changes = @watchlist.items.map { |item| [item.ticker, item.percent_change] }
    render json: { changes: changes.to_h, prefs: prefs }
  end

  private

  def load_watchlist
    @watchlist = Watchlist.find(params[:id])
  end

  def require_owner
    head :forbidden unless @watchlist.owner_id == current_user.id
  end

  def watchlist_params
    params.require(:watchlist).permit!
  end
end
