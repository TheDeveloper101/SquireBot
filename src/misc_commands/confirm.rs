use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use crate::model::containers::ConfirmationsContainer;

#[command("yes")]
#[aliases("y")]
#[help_available(false)]
#[description("Confirms your waiting request.")]
async fn yes(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let todos = data.get::<ConfirmationsContainer>().unwrap();
    if let Some((_, mut task)) = todos.remove(&msg.author.id) {
        task.execute(ctx, msg).await
    } else {
        msg.reply(
            &ctx.http,
            "Its seems that you don't have anything waiting for your approval.",
        )
        .await?;
        Ok(())
    }
}

#[command("no")]
#[aliases("n")]
#[help_available(false)]
#[description("Denies your waiting request.")]
async fn no(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let todos = data.get::<ConfirmationsContainer>().unwrap();
    if let Some((_, task)) = todos.remove(&msg.author.id) {
        msg.reply(&ctx.http, "Alright, I won't do that.").await?;
    } else {
        msg.reply(
            &ctx.http,
            "Its seems that you don't have anything waiting for your approval.",
        )
        .await?;
    }
    Ok(())
}
